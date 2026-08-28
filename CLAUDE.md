# Arcade — Design Rules

This is a children's educational arcade served by a single Flask app (`app.py`). Every game is a **self-contained single HTML file** with all CSS and JS inline. No external JS frameworks. No build step.

---

## Server (`app.py`)

- Flask dev server. Every playable file must be registered in the `GAMES` list — unregistered files are blocked by `_ALLOWED`.
- Each game entry has: `key`, `title`, `desc` (two-line array), `desktop`, `mobile`, `color` (accent hex), `stripe` (gradient string for the hub card).
- API routes all live under `/api/`. Never hard-code data that the server already exposes.

### API endpoints in use

| Endpoint | Used by |
|---|---|
| `GET /api/tts?word=` | Spelling Adventure, Sound Speller — returns MP3 audio |
| `GET /api/word-image?word=` | Sound Speller — DDG image for a word |
| `GET /api/item-sets` | Counting Garden, Math Garden — custom emoji/image sets |
| `GET /api/custom-sets` | Sort It Out — custom sort bins |
| `GET /api/spelling-sets` | Spelling Adventure — custom word lists |
| `GET /api/ss-word-sets` | Sound Speller — custom phonics word sets |
| `GET /api/letter-words` | Letter Draw — words associated with each letter |
| `GET /audio/<id>.mp3` | All games — pre-recorded narration clips |
| `POST /api/recognize-letter` | Letter Draw, Number Draw — Claude Haiku letter/digit recognition |

---

## HTML / CSS rules

### Document head (every game)
```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Game Name</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800;900&display=swap" rel="stylesheet">
```

- `maximum-scale=1.0, user-scalable=no` on every game — prevents accidental pinch-zoom during play.
- Font is always **Nunito** (400 / 700 / 800 / 900 weights). Never use a different font.

### CSS custom properties (`:root`)
Every game defines the same palette tokens:
```css
:root {
  --coral:  #FF6B6B;
  --teal:   #4ECDC4;
  --yellow: #FFE66D;
  --mint:   #A8E6CF;
  --green:  #56c870;
  --purple: #C3A6FF;
  --bg:     #FFF9F0;   /* warm off-white background */
  --ink:    #2D2D3A;   /* near-black text */
}
```
Games may add extra tokens (`--pink`, `--coral`, etc.) for their accent color, but must not redefine the core set.

### Screen management
All games except Sound Speller and Spelling Adventure use the **fixed-screen pattern**:
```css
html, body { height: 100%; width: 100%; overflow: hidden; }
.screen { display: none; position: fixed; inset: 0; flex-direction: column; align-items: center; }
.screen.active { display: flex; }
```
`showScreen(id)` removes `.active` from all screens and adds it to the target. There is always:
- A **splash** screen (settings + PLAY button)
- A **game** screen (the actual gameplay)
- A **win** screen (end-of-game celebration)

Sound Speller uses a scrollable single-page layout (`min-height: 100dvh`). Spelling Adventure uses a card-centered-in-body layout with `overflow-y: auto`.

### Back button
Every game screen has a `←` back button (fixed, top-left, `position: fixed; top: 12px; left: 12px`) that calls `showScreen('splash')`.

### Buttons
- Pill shape: `border-radius: 50px`
- Press effect: `transform: translateY(3px)` on `:active`, shadow reduces from `0 6px 0` to `0 3px 0`
- Option toggles (splash settings): `.opt-btn` with `.selected` class toggled by `pickOpt(el, key)` — updates the `S` object
- Primary action buttons are full-color; secondary/ghost buttons are `background: rgba(255,255,255,.3)`

### Responsive / mobile
- Use `clamp()` for all font sizes that must scale: `font-size: clamp(min, vw, max)`
- Primary breakpoint: `@media (max-width: 600px)` — keyboards, grids, and panels adapt
- Secondary breakpoints: `480px`, `420px`, `380px` as needed
- Keyboard rows: `flex-wrap: nowrap; gap: 3-4px` with `.key { flex: 1; min-width: 0 }` so all keys fit in one row regardless of screen width
- On mobile, game panels go full-width: `border-radius: 0; box-shadow: none; padding: 16px`
- Math Smash uses `@media (max-width: 700px)` to switch from side-by-side to column layout

---

## JavaScript rules

### State objects
Every game uses two module-level objects:
- `S` — **settings** selected on the splash screen (persists between rounds, reflects user choices)
- `G` — **game state** (reset on each `startGame()` call)

### Game loop structure
```
startGame() → G reset → nextRound()
nextRound() → build question → wait for input
correct answer → showFeedback(true) → [if last round] showWin() else nextRound()
wrong answer → showFeedback(false) → retry or next
```

### Scoring
- `G.score` — total correct answers
- `G.firstTry` — correct on first attempt (no wrong guesses)
- Stars at end: `pct = G.firstTry / G.totalRounds` → ⭐ (<60%), ⭐⭐ (60–89%), ⭐⭐⭐ (90%+)
- Live star bar updates via `updateStars()` during gameplay

---

## Audio rules

### Synthesized tones (WebAudio API)
All games use the same `playTone(freq, type, dur, vol, endFreq?)` pattern:
```js
function playTone(freq, type, dur, vol = 0.18, endFreq = null) {
  const ac = getAudio(); // lazy-init AudioContext
  const osc = ac.createOscillator();
  const gain = ac.createGain();
  osc.connect(gain); gain.connect(ac.destination);
  osc.type = type; osc.frequency.value = freq;
  gain.gain.setValueAtTime(vol, ac.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + dur);
  osc.start(); osc.stop(ac.currentTime + dur);
}
```

Standard sound functions every game has:
- `playCorrect()` — ascending 4-note chord: `[523, 659, 784, 1046]` sine, 90ms apart
- `playWrong()` — low square wave: `200Hz`
- `playCelebrate()` — 8-note ascending scale: `[523,587,659,698,784,880,988,1046]`, 75ms apart

### Pre-recorded MP3 clips
Served from `/audio/<id>.mp3`. Used for narration (player turn announcements, read-aloud). Played via:
```js
function playClip(id) {
  try { new Audio(`/audio/${id}.mp3`).play().catch(() => {}); } catch {}
}
```
Always wrap in try/catch and use `.catch(()=>{})` — audio can fail silently.

### TTS
`/api/tts?word=<word>` returns MP3. Used in Spelling Adventure and Sound Speller.

---

## Celebration rules

Every game must celebrate at two moments. Both must be **dynamic** (random choice from a list) and have **sound**.

### Per-round celebration (each correct answer / matched pair / sorted item)
- Show a brief animated toast or overlay — 700–1600ms — then auto-advance
- Message chosen randomly from ≥5 options: `['Amazing!','Great job!','You got it!','Excellent!','Super!']`
- Emoji chosen randomly from: `['🌟','🎉','⭐','🌻','🥳']`
- Sound: `playCorrect()` or a chime
- Toast pattern: `position: fixed; border-radius: 50px; animation: toastPop` — scales in, floats up, fades out

### End-of-level celebration (win screen)
- `showWin()` always calls `playCelebrate()` then `spawnConfetti()`
- Win screen shows: title, ⭐/⭐⭐/⭐⭐⭐ based on `firstTry` pct, dynamic sub-message, stat line, "Play Again" + "Change Settings" buttons
- Confetti: 60 `<div class="confetti">` elements, random colors from the palette, staggered `setTimeout` spawn, `animation: confettiFall` keyframe
- Sub-message is score-reactive: perfect → "Perfect [verb]!", good → "Great [verb]!", low → "Keep practising!"

### Milestone celebration (Sound Speller only)
Every 10 words solved → `showLevelComplete()` overlay with a random icon, "N Words Solved!" title, random hype message, 5-note ascending fanfare (`[523,659,784,1047,1319]`), and a "Keep Going!" dismiss button.

---

## Custom content (sort_set_builder)

`sort_set_builder.html` is the admin tool for managing custom content shared across games:

| Section | API | Consumed by |
|---|---|---|
| Sort Bins | `/api/custom-sets` | Sort It Out |
| Item Sets | `/api/item-sets` | Counting Garden, Math Garden |
| Spelling Words | `/api/spelling-sets` | Spelling Adventure |
| Sound Speller Words | `/api/ss-word-sets` | Sound Speller |

Custom sets are stored in `custom_sets.json`. Images are fetched from DuckDuckGo and cached in `img_cache/`.

---

## Game catalog

| File | Title | Type |
|---|---|---|
| `racer.html` | Endless Runner | Arcade |
| `maze_muncher.html` | Maze Muncher | Arcade |
| `big_green.html` | Big Green | Platformer |
| `math_smash.html` | Math Smash | Educational |
| `letter_draw.html` | Letter Draw | Educational |
| `spelling_adventure.html` | Spelling Adventure | Educational |
| `memory_match.html` | Memory Match | Educational |
| `counting_game.html` | Counting Garden | Educational |
| `math_garden.html` | Math Garden | Educational |
| `sort_game.html` | Sort It Out | Educational |
| `shape_shift.html` | Shape Shift | Educational |
| `vocab_builder.html` | Vocab Builder | Educational |
| `sound_speller.html` | Sound Speller | Educational |
| `pip_the_bear.html` | Pip the Bear | Story |
| `sing_along.html` | Sing-Along Studio | Educational |
| `number_draw.html` | Number Draw | Educational |
| `pattern_party.html` | Pattern Party | Educational |

---

## What NOT to do

- Do not use React, Vue, or any JS framework
- Do not add `<script src="...">` CDN dependencies (exception: Google Fonts CSS is fine)
- Do not create separate CSS or JS files — everything stays inline in the HTML
- Do not create a new game file without registering it in `GAMES` in `app.py`
- Do not use `user-scalable=yes` — pinch-zoom breaks touch gameplay
- Do not use a different font — Nunito is the identity of the arcade
- Do not skip the `try/catch` wrapper on Audio API calls
- Do not add a celebration that has no sound, or sound with no visual
