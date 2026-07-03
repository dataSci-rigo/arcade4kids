#!/usr/bin/env python3
"""
Download and cache all Math Smash background images from Unsplash.
Images are saved to img_cache/math_smash/scene_N.jpg (one per scene, 0-indexed).
Run this once; re-running skips already-downloaded files.
"""

import os
import sys
import urllib.request

SCENES = [
    ("Underwater Reef",   "1583212292454-1fe6229603b7"),
    ("Outer Space",       "1419242902214-272b3f66ee7a"),
    ("Enchanted Forest",  "1441974231531-c6227db76b6e"),
    ("Castle Hall",       "1533154683836-84ea7a0bc310"),
    ("Rainbow Meadow",    "1500382017468-9049fed747ef"),
    ("Volcano Island",    "1559827260-dc66d52bef19"),
    ("Arctic Tundra",     "1478860409698-8707f313ee8b"),
    ("Desert Oasis",      "1509316785289-025f5b846b35"),
    ("Cloud Kingdom",     "1502134249126-9f3755a50d78"),
    ("Mushroom Village",  "1518531933037-91b2f5f229cc"),
    ("Crystal Cave",      "1474487548417-781cb71495f3"),
    ("Ancient Temple",    "1539768942893-daf53e448371"),
    ("Tropical Beach",    "1507525428034-b723cf961d3e"),
    ("Mountain Peak",     "1506905925346-21bda4d32df4"),
    ("Autumn Forest",     "1507003211169-0a1dd7228f2d"),
    ("Night Market",      "1573455494060-c5595004fb6c"),
    ("Magic Library",     "1521587760476-6c12a4b040da"),
    ("Pirate Ship",       "1505142468610-359e7d316be0"),
    ("Dragon's Lair",     "1519074069444-1ba4fff66d16"),
    ("Futuristic City",   "1480714378408-67cf0d13bc1b"),
]

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "img_cache", "math_smash")
os.makedirs(CACHE_DIR, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (arcade-cache-bot/1.0)"}

def download(idx, name, photo_id):
    dest = os.path.join(CACHE_DIR, f"scene_{idx}.jpg")
    if os.path.isfile(dest):
        print(f"  [{idx:02d}] {name} — already cached, skipping")
        return True
    url = f"https://images.unsplash.com/photo-{photo_id}?w=1200&q=80&fit=crop"
    print(f"  [{idx:02d}] {name} — downloading…", end=" ", flush=True)
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        with open(dest, "wb") as f:
            f.write(data)
        print(f"done ({len(data)//1024} KB)")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

print(f"Saving to: {CACHE_DIR}\n")
ok = sum(download(i, name, pid) for i, (name, pid) in enumerate(SCENES))
print(f"\n{ok}/{len(SCENES)} images ready.")
if ok < len(SCENES):
    print("Re-run to retry failed downloads.")
    sys.exit(1)
