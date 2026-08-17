# Tests

```bash
pytest                  # fast tiers, ~1.5s
pytest -m browser       # Playwright input matrix, ~2min
python tests/diagnose_input.py   # regenerate INPUT_MATRIX.md
```

One-time setup: `pip install -r requirements-dev.txt && playwright install chromium`.

## Why this suite exists

Two shipped bugs it would have caught the day they landed:

- `serve_audio`'s guard was `[a-z0-9_]+\.mp3`, which rejected both the `/` and
  the uppercase digraph names in `/audio/phonemes/SH.mp3`. All 43 phoneme clips
  404'd and Sound Speller's core mechanic was silently dead.
- Nine games had no `keydown` handler at all, and Memory Match built its cards
  as plain `<div>`s bound with `addEventListener` — so it could not be played
  with a keyboard, at all, by anyone.

Neither is a logic error. Both are *contract drift* between a route guard, an
asset on disk, and what a game actually requests — which is what these tests
pin down.

## Layout

| File | Covers |
|---|---|
| `baseline.py` | Tier map, control schemes, documented exemptions. Single source of truth. |
| `conftest.py` | Safety fixtures — data isolation, network kill-switch, live server, shared browser. |
| `browser_util.py` | Playwright helpers + the `addEventListener` instrumentation. |
| `test_input.py` | ★ keyboard + touch parity per game, desktop and mobile. |
| `test_assets.py` | Every mp3/image resolves through its route; clip families have no gaps. |
| `test_routes.py` | File-serving guards, path traversal. |
| `test_api.py` | JSON contracts; the four-set-types-one-file clobber risk. |
| `test_helpers.py` | `_slugify`, `_build_rounds`, `_cache_image`. |
| `test_registry.py` | `GAMES` integrity, orphan `.html` detection. |
| `diagnose_input.py` | Not a test — regenerates `INPUT_MATRIX.md`. |

## Three rules

1. **Never mutate real data.** `custom_sets.json`, `settings.json`, and
   `vocab.db` came off a flash-drive backup and are not reproducible. Writing
   tests must use the `isolated_data` fixture; `data_files_unchanged` hashes
   them and fails the run if anything moved.
2. **Never touch the network** — `no_network` is autouse.
3. **Never make a billable API call** — `no_anthropic` is autouse.

## How input support is measured

Watching the DOM is not enough: a canvas game reacting to `ArrowLeft` only
mutates a JS variable, and half the games bind clicks with `addEventListener`
rather than an `onclick` attribute. So `browser_util` instruments
`EventTarget.prototype.addEventListener` **before page scripts run**, records
every registration, and counts real handler invocations. "Keydown fired" then
means game code actually ran.

## CLAUDE.md is aspirational

It describes an ideal only ~5 of 15 files meet, and only one of three real
tiers (retro arcade / educational / admin tool). `baseline.py` records what is
true today so the suite is green on a clean checkout and fails on *new* drift.
Raising the bar is a product decision — make it there, not by loosening a test.
