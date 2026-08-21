#!/usr/bin/env python3
"""
Generate Math Smash scene backgrounds with GenAI, replacing the Unsplash photos.

Two engines, keys read from ~/Documents/.env:
  flux  — Replicate, black-forest-labs/flux-dev   (key: REPLICATE,   ~$0.025/img)
  nano  — OpenRouter, google/gemini-2.5-flash-image (key: OPEN_ROUTER, ~$0.035/img)
          supports --style-ref for style-consistent generation

Workflow:
  1. Pick an anchor style (a few candidates for one scene):
       conda run -n p312 python gen_images_math_smash.py candidates --scenes 0 --count 4
  2. Look at img_cache/math_smash_candidates/candidates.html, pick a favorite.
  3. Generate everything else in the same style (nano engine only):
       conda run -n p312 python gen_images_math_smash.py candidates \
           --engine nano --style-ref img_cache/math_smash_candidates/scene_00_nano_2.png
  4. Install winners (backs up the old Unsplash file on first replace):
       conda run -n p312 python gen_images_math_smash.py install 0 scene_00_nano_2.png

The install step center-crops to 4:3, resizes to 1200x900, and saves JPEG q82 —
the exact shape math_smash.html serves from img_cache/math_smash/scene_N.jpg.
"""

import argparse
import base64
import json
import re
import shutil
import sys
import time
import urllib.request
from pathlib import Path

BASE_DIR   = Path(__file__).resolve().parent
MASTER_ENV = Path.home() / "Documents" / ".env"
CAND_DIR   = BASE_DIR / "img_cache" / "math_smash_candidates"
SCENE_DIR  = BASE_DIR / "img_cache" / "math_smash"
BACKUP_DIR = SCENE_DIR / "backup_unsplash"

# One shared style so all 20 scenes read as one game. Scenery only: the game
# overlays characters, decos, and a gradient on top of the image.
STYLE = (
    "Soft storybook illustration for a children's math game, bright saturated "
    "colors, gentle painterly texture, warm and friendly atmosphere, wide "
    "scenic background with open space in the middle, no people, no animals, "
    "no characters, no text, no letters, no watermark."
)

# Order must match SCENES in math_smash.html / fetch_images_math_smash.py.
SCENES = [
    ("Underwater Reef",  "colorful coral reef under clear blue water, sun rays filtering down, bubbles"),
    ("Outer Space",      "deep space with swirling nebulas, planets and twinkling stars"),
    ("Enchanted Forest", "magical glowing forest with giant ancient trees and floating light sparkles"),
    ("Castle Hall",      "grand fairytale castle hall with banners, columns and stained glass windows"),
    ("Rainbow Meadow",   "rolling flower meadow under a huge rainbow, fluffy clouds"),
    ("Volcano Island",   "tropical volcanic island with gentle lava glow and palm trees, dramatic sky"),
    ("Arctic Tundra",    "sparkling snowy landscape with ice formations and northern lights"),
    ("Desert Oasis",     "desert oasis with palm trees, clear turquoise pool and golden dunes"),
    ("Cloud Kingdom",    "kingdom of fluffy clouds in a pastel sky, floating cloud castles"),
    ("Mushroom Village", "cozy village of giant colorful mushroom houses in a mossy glade"),
    ("Crystal Cave",     "cave filled with giant glowing rainbow crystals"),
    ("Ancient Temple",   "mysterious ancient stone temple overgrown with vines, shafts of light"),
    ("Tropical Beach",   "tropical beach with soft white sand, turquoise sea and palm trees"),
    ("Mountain Peak",    "view from a high mountain peak above the clouds at golden hour"),
    ("Autumn Forest",    "autumn forest with red and gold falling leaves on a winding path"),
    ("Night Market",     "festive night market street glowing with colorful paper lanterns"),
    ("Magic Library",    "enormous magical library with tall bookshelves and floating glowing books"),
    ("Pirate Ship",      "wooden pirate ship deck with sails and rigging on a sunny sea"),
    ("Dragon's Lair",    "friendly dragon's mountain lair with piles of gold treasure, warm light"),
    ("Futuristic City",  "bright futuristic city skyline with flying vehicles and neon lights"),
]

USD_PER_IMAGE = {"flux": 0.025, "nano": 0.035}


# ── keys ──────────────────────────────────────────────────────────────────────

def read_key(name: str) -> str:
    if MASTER_ENV.exists():
        for line in MASTER_ENV.read_text().splitlines():
            m = re.match(rf"^{name}=(.*)$", line.strip())
            if m:
                return m.group(1).strip().strip("'\"")
    print(f"ERROR: {name} not found in {MASTER_ENV}")
    sys.exit(1)


# ── http ──────────────────────────────────────────────────────────────────────

def http_json(url: str, payload: dict, headers: dict, timeout: int = 180) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def http_get(url: str, headers: dict | None = None, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


# ── engines ───────────────────────────────────────────────────────────────────

def gen_flux(prompt: str, n: int) -> list[bytes]:
    """Replicate flux-dev: one prediction, up to 4 outputs."""
    token = read_key("REPLICATE")
    out: list[bytes] = []
    while len(out) < n:
        batch = min(4, n - len(out))
        pred = http_json(
            "https://api.replicate.com/v1/models/black-forest-labs/flux-dev/predictions",
            {"input": {"prompt": prompt, "aspect_ratio": "4:3", "num_outputs": batch,
                       "output_format": "jpg", "output_quality": 88}},
            {"Authorization": f"Bearer {token}", "Prefer": "wait=60"},
        )
        # Poll if the wait window expired before completion
        while pred.get("status") in ("starting", "processing"):
            time.sleep(2)
            pred = json.loads(http_get(pred["urls"]["get"],
                                       {"Authorization": f"Bearer {token}"}))
        if pred.get("status") != "succeeded":
            raise RuntimeError(f"Replicate prediction {pred.get('status')}: {pred.get('error')}")
        urls = pred["output"] if isinstance(pred["output"], list) else [pred["output"]]
        out += [http_get(u) for u in urls]
    return out[:n]


def gen_nano(prompt: str, n: int, style_ref: Path | None) -> list[bytes]:
    """OpenRouter gemini-2.5-flash-image: one image per call; optional style ref."""
    token = read_key("OPEN_ROUTER")
    content: list[dict] = [{"type": "text", "text": prompt}]
    if style_ref:
        mime = "image/png" if style_ref.suffix == ".png" else "image/jpeg"
        b64 = base64.b64encode(style_ref.read_bytes()).decode()
        content.insert(0, {"type": "image_url",
                           "image_url": {"url": f"data:{mime};base64,{b64}"}})
        content[1]["text"] = (
            "Use the attached image ONLY as an art style reference: copy its "
            "brushwork, color treatment and rendering. Do NOT copy any objects, "
            "scenery or subject matter from it — the new image must contain "
            "none of the reference's content. Draw a completely different "
            "scene, in landscape 4:3 orientation: " + prompt)
    out = []
    for _ in range(n):
        resp = http_json(
            "https://openrouter.ai/api/v1/chat/completions",
            {"model": "google/gemini-2.5-flash-image",
             "modalities": ["image", "text"],
             "messages": [{"role": "user", "content": content}]},
            {"Authorization": f"Bearer {token}"},
        )
        try:
            data_url = resp["choices"][0]["message"]["images"][0]["image_url"]["url"]
        except (KeyError, IndexError):
            raise RuntimeError(f"No image in OpenRouter response: {json.dumps(resp)[:400]}")
        out.append(base64.b64decode(data_url.split(",", 1)[1]))
    return out


# ── contact sheet ─────────────────────────────────────────────────────────────

def write_sheet() -> None:
    rows = []
    files = sorted(CAND_DIR.glob("scene_*.*"))
    by_scene: dict[int, list[Path]] = {}
    for f in files:
        m = re.match(r"scene_(\d+)_", f.name)
        if m:
            by_scene.setdefault(int(m.group(1)), []).append(f)
    for idx in sorted(by_scene):
        name = SCENES[idx][0] if idx < len(SCENES) else f"scene {idx}"
        cells = "".join(
            f'<figure><img src="{f.name}" loading="lazy">'
            f'<figcaption>{f.name}<br>'
            f'<code>python gen_images_math_smash.py install {idx} {f.name}</code>'
            f'</figcaption></figure>'
            for f in by_scene[idx])
        rows.append(f"<h2>{idx:02d} — {name}</h2><div class=row>{cells}</div>")
    (CAND_DIR / "candidates.html").write_text(
        "<!doctype html><meta charset=utf-8><title>Math Smash candidates</title>"
        "<style>body{font-family:sans-serif;background:#222;color:#eee;padding:16px}"
        ".row{display:flex;gap:10px;flex-wrap:wrap}figure{margin:0;width:320px}"
        "img{width:100%;border-radius:8px}figcaption{font-size:11px;padding:4px 0}"
        "code{background:#333;padding:1px 4px;border-radius:4px;display:inline-block;"
        "margin-top:2px;font-size:10px}</style>" + "".join(rows))
    print(f"\nContact sheet: {CAND_DIR / 'candidates.html'}")


# ── commands ──────────────────────────────────────────────────────────────────

def cmd_candidates(args) -> None:
    CAND_DIR.mkdir(parents=True, exist_ok=True)
    style_ref = Path(args.style_ref).resolve() if args.style_ref else None
    if style_ref and not style_ref.exists():
        print(f"ERROR: style ref {style_ref} not found"); sys.exit(1)
    if style_ref and args.engine != "nano":
        print("ERROR: --style-ref only works with --engine nano"); sys.exit(1)

    if args.scenes == "all":
        scene_ids = list(range(len(SCENES)))
    else:
        scene_ids = [int(s) for s in args.scenes.split(",")]

    total = len(scene_ids) * args.count
    print(f"Engine : {args.engine}  |  scenes: {scene_ids}  |  {args.count} candidates each")
    print(f"Total  : {total} images ≈ ${total * USD_PER_IMAGE[args.engine]:.2f}")
    if style_ref:
        print(f"Style  : matching {style_ref.name}")
    print()

    for idx in scene_ids:
        name, desc = SCENES[idx]
        prompt = f"{desc}. {STYLE}"
        print(f"[{idx:02d}] {name} …", flush=True)
        try:
            imgs = (gen_flux(prompt, args.count) if args.engine == "flux"
                    else gen_nano(prompt, args.count, style_ref))
        except Exception as e:
            print(f"     FAILED: {e}")
            continue
        for k, data in enumerate(imgs):
            ext = "png" if data[:8] == b"\x89PNG\r\n\x1a\n" else "jpg"
            dest = CAND_DIR / f"scene_{idx:02d}_{args.engine}_{k}.{ext}"
            dest.write_bytes(data)
            print(f"     saved {dest.name} ({len(data)//1024} KB)")
    write_sheet()


def cmd_install(args) -> None:
    from PIL import Image
    src = CAND_DIR / args.candidate
    if not src.exists():
        src = Path(args.candidate)
    if not src.exists():
        print(f"ERROR: candidate {args.candidate} not found"); sys.exit(1)

    dest = SCENE_DIR / f"scene_{args.scene}.jpg"
    if dest.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        bak = BACKUP_DIR / dest.name
        if not bak.exists():
            shutil.copy2(dest, bak)
            print(f"  backed up old → {bak.relative_to(BASE_DIR)}")

    img = Image.open(src).convert("RGB")
    w, h = img.size
    # center-crop to 4:3 then resize to the shape the game already serves
    target = 4 / 3
    if w / h > target:
        new_w = int(h * target); x = (w - new_w) // 2; img = img.crop((x, 0, x + new_w, h))
    elif w / h < target:
        new_h = int(w / target); y = (h - new_h) // 2; img = img.crop((0, y, w, y + new_h))
    img = img.resize((1200, 900), Image.LANCZOS)
    img.save(dest, "JPEG", quality=82, optimize=True, progressive=True)
    print(f"  ✓ installed {src.name} → {dest.relative_to(BASE_DIR)} "
          f"({dest.stat().st_size//1024} KB)")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("candidates", help="generate candidate images")
    c.add_argument("--engine", choices=("flux", "nano"), default="flux")
    c.add_argument("--scenes", default="all", help='"all" or comma list, e.g. 0,3,14')
    c.add_argument("--count", type=int, default=3, help="candidates per scene (default 3)")
    c.add_argument("--style-ref", help="reference image for style consistency (nano only)")
    c.set_defaults(fn=cmd_candidates)

    i = sub.add_parser("install", help="promote a candidate to img_cache/math_smash/")
    i.add_argument("scene", type=int)
    i.add_argument("candidate", help="filename in the candidates dir")
    i.set_defaults(fn=cmd_install)

    s = sub.add_parser("sheet", help="rebuild candidates.html only")
    s.set_defaults(fn=lambda a: write_sheet())

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
