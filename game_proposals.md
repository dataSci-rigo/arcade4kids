# New Game Proposals

Ranked by value ÷ effort. Companion to [future_projects.md](future_projects.md),
which holds finished song lyrics and other raw content waiting for a game.

## Where the catalog stands

| Category | Games | Count |
|---|---|---|
| Arcade | Endless Runner, Maze Muncher, Big Green | 3 |
| Math | Math Smash, Math Garden, Counting Garden | 3 |
| Literacy | Letter Draw, Spelling Adventure, Sound Speller, Vocab Builder | 4 |
| Logic | Memory Match, Sort It Out, Shape Shift | 3 |
| Story | Pip the Bear | 1 |
| Admin | Custom Items Builder | 1 |

**Uncovered:** music/rhythm, time & clocks, money, patterns/sequencing, rhyming.
Every math game is multiple-choice — nothing teaches writing a numeral.

> **Build rule for all of these:** keyboard and touch from day one. Nine games
> shipped keyboard-dead and had to be retrofitted; the suite in `tests/` now
> fails any game that repeats it. See "Controls" in each proposal.

---

## 1. Sing-Along Studio ⭐ highest value

**The content already exists.** `future_projects.md` holds five finished
original songs — *Flitter, Little Bat*, *Squeaky, Squeaky Little Bat*,
*Carlitos Lunagen*, *Rice Is Nice*, *Naptime Adventure* — written and unused.
Music and rhythm are entirely absent from the arcade.

- **Teaches:** phonological awareness (the strongest pre-reading predictor),
  rhythm, memory, vocabulary.
- **Reuses:** `tts_build.py` to generate sung/spoken lines into `audio/`; the
  standard WebAudio `playTone()` for melody; the splash/game/win screen
  pattern; existing confetti and celebration helpers.
- **New API:** none. Clips are static files under `/audio/`, exactly like the
  217 already there.
- **Mechanic:** lyrics scroll with a bouncing-ball highlight; the child taps or
  presses Space on the beat; end-of-song stars scored on timing accuracy. A
  "just listen" mode with no scoring for the youngest kids.
- **Controls:** Space/Enter to tap the beat, arrows to pick a song, tap anywhere
  on the lyric card for touch.
- **Effort:** medium — one HTML file plus a `tts_build.py` run. The expensive
  part, writing singable original verse, is done.

## 2. Number Draw ⭐ cheapest win

Letter Draw already does handwriting recognition through Claude Haiku. The same
canvas, scoring, and celebration work unchanged for digits.

- **Teaches:** numeral formation 0–9 — the one math skill the arcade misses,
  since Math Smash, Math Garden, and Counting Garden are all multiple-choice.
- **Reuses:** `letter_draw.html` nearly wholesale; `/api/recognize-letter`.
- **New API:** none, but one backend change — that route's guard at
  [app.py:1210](app.py#L1210) currently requires `len(target) == 1 and
  target.isalpha()`, so digits are rejected. Relax to accept `0-9` and adjust
  the prompt wording from "letter" to "digit". `tests/test_api.py` pins the
  current behaviour, so that test updates alongside the change.
- **Extension:** trace a numeral, then draw that many objects — links symbol to
  quantity.
- **Controls:** canvas is a legitimate pointer surface; digit keys 0–9 select
  the target, Enter submits, so it is playable without drawing on desktop.
- **Effort:** low.

## 3. Time Teller

Clock reading has zero coverage and is core kindergarten curriculum.

- **Teaches:** analog clock reading, o'clock → half past → quarter hours,
  sequencing daily events.
- **Reuses:** screen pattern, palette, celebration helpers.
- **New API:** none — an inline SVG clock with draggable hands, fully client-side.
- **Mechanic:** three modes — read the clock and pick the time; set the hands to
  a given time; order daily events (breakfast, school, bedtime).
- **Controls:** drag or tap the hands; arrows nudge the selected hand by 5
  minutes, Tab switches hour/minute hand, Enter commits.
- **Effort:** low–medium. Hand-dragging maths is the only fiddly part.

## 4. Pattern Party

AB / AAB / ABC pattern completion — a classic pre-K logic skill, absent today.

- **Teaches:** sequencing, prediction, early algebraic thinking.
- **Reuses:** `/api/item-sets` imagery (shared with Counting Garden and Math
  Garden) and Sort It Out's drag mechanics. Note `item_sets` is currently empty
  post-restore, so this pairs well with rebuilding it in the Custom Items Builder.
- **New API:** none.
- **Mechanic:** a strip of items with gaps; drag or press the item that comes
  next; difficulty escalates AB → AAB → ABC → ABBC.
- **Controls:** digits 1–9 pick from the tray, arrows move the highlight, Enter
  places. Drag for touch.
- **Effort:** low–medium.

## 5. Coin Counter

- **Teaches:** coin recognition, counting by 5s/10s/25s, making amounts.
- **Reuses:** Counting Garden's proven count-and-check model; SVG coins mean no
  image fetching at all.
- **New API:** none.
- **Mechanic:** "make 30¢" — tap coins into a purse; running total shown; later
  levels remove the running total.
- **Controls:** number keys select a coin denomination, Enter adds, Backspace
  removes.
- **Effort:** low.

---

## Cheap follow-ons

- **Rhyme Time** — word families (`-at`, `-ig`, `-op`). Reuses `/api/tts` and
  the 43 phoneme clips already in `audio/phonemes/`. Slots neatly between Sound
  Speller and Spelling Adventure in the phonics ladder.
- **A second Pip book** — the picture-book-with-questions format is proven and
  structurally reusable; only art and text change.

## Deliberately not proposed

- **Typing games** — the target age (3–6) can't reach home row.
- **Anything needing a new AI endpoint** — Letter Draw and Vocab Builder already
  cover that ground, and each call costs money per child per round.
