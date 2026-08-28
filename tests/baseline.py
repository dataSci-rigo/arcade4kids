"""Ground truth about the arcade, in one place.

CLAUDE.md describes an ideal the codebase does not actually meet — enforcing it
literally fails 11 of 16 files. This module records what is *true today*, so the
suite goes green on a clean checkout and fails only on NEW drift.

When a game is fixed, flip its entry here; the tests follow automatically.
"""

# ── Tiers ────────────────────────────────────────────────────────────────────
# Retro arcade: canvas-driven, monospace/Press Start 2P, no .screen pattern,
# no palette tokens. A deliberate and different visual language.
TIER_ARCADE = {'racer.html', 'maze_muncher.html', 'big_green.html'}

# Educational: the .screen + showScreen() games.
TIER_EDU = {
    'counting_game.html', 'math_garden.html', 'math_smash.html',
    'memory_match.html', 'shape_shift.html', 'sort_game.html',
    'sound_speller.html', 'spelling_adventure.html', 'vocab_builder.html',
    'letter_draw.html', 'pip_the_bear.html', 'sing_along.html',
    'number_draw.html', 'pattern_party.html',
}

# Admin tool: no screens, no back button, no viewport lock. Not a game.
TIER_ADMIN = {'sort_set_builder.html'}

ALL_PLAYABLE = TIER_ARCADE | TIER_EDU

# Root *.html files that are intentionally not registered in GAMES.
# arcade.html was deleted (unregistered orphan, superseded by templates/index.html).
KNOWN_ORPHANS: set[str] = set()

# ── Accepted deviations from CLAUDE.md ───────────────────────────────────────
# Missing `user-scalable=no`. Reviewed and accepted by the owner — not a finding.
VIEWPORT_EXEMPT = {'big_green.html', 'sort_set_builder.html'}

# Fonts. The arcade tier is deliberately retro; the admin tool is not a game.
FONT_EXEMPT = TIER_ARCADE | TIER_ADMIN

# Palette tokens (--coral etc). Arcade tier uses its own retro palette.
PALETTE_EXEMPT = TIER_ARCADE | TIER_ADMIN | {'shape_shift.html', 'vocab_builder.html'}

# Celebration helpers (playCorrect/playCelebrate/spawnConfetti). Only 5 of 16
# games implement the full set today. Locked at current state; raising this bar
# is a product decision, not a test failure.
CELEBRATION_REQUIRED = {
    'counting_game.html', 'math_garden.html', 'memory_match.html',
    'pip_the_bear.html', 'sort_game.html', 'sing_along.html',
    'number_draw.html', 'pattern_party.html',
}

# ── Audio ────────────────────────────────────────────────────────────────────
# Dev-only accent samples from voice selection. Nothing requests them, and
# serve_audio's hyphen-free guard rejects them. Excluded deliberately rather
# than widening the route regex for unused files.
AUDIO_EXCLUDE_PREFIXES = ('test-',)

# Clip families built from template literals in game JS. Expanded and checked
# for gaps by test_assets.py.
CLIP_FAMILIES = {
    # math_smash.html:1404  playClip(`ms_scene_${curSceneIdx}_${charKey}`)
    'ms_scene': [f'ms_scene_{i}_{c}' for i in range(20)
                 for c in ('finn', 'lily', 'zara', 'rex')],
    # counting_game.html:588  playClip(`skip_by_${G.step}`)
    'skip_by': [f'skip_by_{n}' for n in (1, 2, 3, 4)],
    # sing_along.html playLine: new Audio(`/audio/sing_${S.song}_${i}.mp3`)
    'sing': [f'sing_{k}_{i}'
             for k, n in (('flitter', 18), ('squeaky', 18), ('carlitos', 16),
                          ('rice', 16), ('naptime', 16))
             for i in range(n)],
}

# ── Screen / control selectors, per game ─────────────────────────────────────
# Discovered by inspection; used to drive the browser tiers.
class Game:
    def __init__(self, file, start, splash='#splash', play='#game',
                 keyboard=None, kb_reason=None, tap=None):
        self.file = file
        self.start = start          # selector that begins play
        self.splash = splash        # container visible before start
        self.play = play            # container visible during play
        self.keyboard = keyboard    # keys that should drive gameplay
        self.kb_reason = kb_reason  # why keyboard is unsupported (None = supported)
        self.tap = tap              # selector for a gameplay control to tap

    @property
    def has_keyboard(self):
        return self.kb_reason is None


# Pointer surfaces that are legitimately not keyboard controls: a drawing or
# steering area, or a touch overlay that duplicates a key binding which already
# works. Exempt from the "every control must be focusable" rule.
POINTER_SURFACES = {
    'canvas',
    'div#touch-left',   # racer: duplicates ArrowLeft, which works
    'div#touch-right',  # racer: duplicates ArrowRight, which works
}

_START = '[onclick="startGame()"]'

GAMES = [
    # ── Retro arcade: keyboard already works ──
    Game('racer.html', '#play-btn', '#menu', '#game',
         keyboard=['ArrowLeft', 'ArrowRight', 'Space'], tap='#touch-left'),
    Game('maze_muncher.html', '#btnStart', '#menu', '#game',
         keyboard=['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'],
         tap='#dpad button[data-dir="left"]'),
    Game('big_green.html', '#startBtn', '#menu', '#game',
         keyboard=['ArrowLeft', 'ArrowRight', 'Space'], tap='canvas'),

    # ── Educational: keyboard already works ──
    Game('math_smash.html', _START, '#splash', '#game',
         keyboard=['1', '2', '3', 'Backspace'], tap='.nb'),
    Game('spelling_adventure.html', _START, '#splash', '#game',
         keyboard=['a', 'b', 'Enter'], tap='.key'),
    Game('sing_along.html', _START, '#splash', '#game',
         keyboard=['Space', 'Enter'], tap='#tap-pad'),
    # Enter checks, Backspace/C clears, G toggles guide; canvas is pointer-only
    Game('number_draw.html', _START, '#splash', '#game',
         keyboard=['g', 'Backspace']),
    # startGame() opens the level menu; letters/numbers tiers take typed input
    Game('pattern_party.html', _START, '#splash', '#menu',
         keyboard=['ArrowRight', 'Enter'], tap='.tier-level'),

    # ── Educational: NO keyboard support (the gap being fixed) ──
    Game('counting_game.html', _START, '#splash', '#game',
         kb_reason='no keydown handler'),
    Game('math_garden.html', _START, '#splash', '#game',
         kb_reason='no keydown handler'),
    Game('memory_match.html', _START, '#splash', '#game',
         kb_reason='cards are createElement("div"), not focusable'),
    Game('shape_shift.html', _START, '#screen-splash', '#screen-game',
         kb_reason='no keydown handler'),
    Game('sort_game.html', _START, '#splash', '#game',
         kb_reason='no keydown handler'),
    Game('sound_speller.html', _START, '#splash', '#game',
         kb_reason='no keydown handler', tap='#play'),
    # Fetches /api/vocab/level on start, so the round takes a beat to render.
    Game('vocab_builder.html', _START, '#screen-splash', '#screen-game',
         kb_reason='no keydown handler', tap='.choice-card'),
    Game('letter_draw.html', _START, '#splash', '#game',
         kb_reason='no keydown handler; canvas tracing is pointer-only'),
    Game('pip_the_bear.html', '#start-btn', '#splash', '#book',
         kb_reason='no keydown handler'),
]

GAMES_BY_FILE = {g.file: g for g in GAMES}

DESKTOP = {'width': 1280, 'height': 800}
MOBILE = {'width': 390, 'height': 844}
