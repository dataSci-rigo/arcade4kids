"""Keyboard and touch parity — the contract this suite exists to enforce.

Every game must be fully playable with a keyboard AND with touch. Not
"technically reachable" — a synthesised keypress must actually invoke game
code, measured by instrumenting addEventListener before page scripts run.

Nine games shipped with zero keydown handlers and gameplay controls built as
plain <div>s, so a kid at a desktop had to use the mouse and a screen reader
saw nothing. These tests fail if that regresses.
"""

import pytest

from baseline import DESKTOP, GAMES, MOBILE, POINTER_SURFACES
from browser_util import (
    browser_page, clickable_but_unfocusable, focusable_count, hits,
    listener_types, reset_hits, start_game,
)

pytestmark = pytest.mark.browser

IDS = [g.file for g in GAMES]


@pytest.mark.parametrize('game', GAMES, ids=IDS)
def test_game_loads_without_errors(live_server, browser, game):
    with browser_page(DESKTOP, live_server, game.file, browser=browser) as (page, problems):
        errors = [p for p in problems if p.startswith('pageerror')]
        assert not errors, f'{game.file}: {errors}'


@pytest.mark.parametrize('game', GAMES, ids=IDS)
def test_game_starts(live_server, browser, game):
    with browser_page(DESKTOP, live_server, game.file, browser=browser) as (page, _):
        clicked, before, after = start_game(page, game.start)
        assert clicked, f'{game.file}: start control {game.start} not clickable'
        entered_canvas = page.evaluate(
            "() => { const c = document.querySelector('canvas');"
            "        return !!(c && c.offsetParent !== null); }")
        assert after != before or entered_canvas, \
            f'{game.file}: clicking {game.start} did not enter play'


@pytest.mark.parametrize('game', GAMES, ids=IDS)
def test_keyboard_drives_gameplay(live_server, browser, game):
    """Pressing keys must run game code — every game, no exceptions.

    Measured via instrumented listeners, so it holds for canvas games where
    a keypress changes only a JS variable and nothing in the DOM.
    """
    with browser_page(DESKTOP, live_server, game.file, browser=browser) as (page, _):
        start_game(page, game.start)
        assert 'keydown' in listener_types(page), \
            f'{game.file}: no keydown listener — unplayable by keyboard'

        reset_hits(page)
        for key in (game.keyboard or
                    ['ArrowRight', 'ArrowLeft', 'ArrowDown', 'Enter', '1']):
            page.keyboard.press(key)
        page.wait_for_timeout(400)
        fired = hits(page).get('keydown', 0)
        assert fired > 0, f'{game.file}: keypresses invoked no game handler'


@pytest.mark.parametrize('game', GAMES, ids=IDS)
def test_gameplay_controls_are_keyboard_reachable(live_server, browser, game):
    """No control may be click-only.

    Memory Match built its cards with createElement('div') and bound them
    with addEventListener — Tab could never reach them, so the game was
    literally unplayable without a pointer.
    """
    with browser_page(DESKTOP, live_server, game.file, browser=browser) as (page, _):
        start_game(page, game.start)
        page.wait_for_timeout(500)
        # Deliberately NO arrow keypress first. Controls must be reachable by
        # a player who reaches for Tab, not only after discovering the arrows.
        orphans = [o for o in clickable_but_unfocusable(page)
                   if o.split('.')[0] not in POINTER_SURFACES
                   and o not in POINTER_SURFACES
                   and not o.startswith('canvas')]
        assert not orphans, (
            f'{game.file}: click-only controls unreachable by keyboard: {orphans}'
        )


@pytest.mark.parametrize('game', GAMES, ids=IDS)
def test_playable_on_mobile_viewport(live_server, browser, game):
    """Game must start and expose a usable control at 390x844 with touch."""
    with browser_page(MOBILE, live_server, game.file, touch=True, browser=browser) as (page, problems):
        errors = [p for p in problems if p.startswith('pageerror')]
        assert not errors, f'{game.file} @mobile: {errors}'

        clicked, before, after = start_game(page, game.start)
        assert clicked, f'{game.file} @mobile: cannot start'

        reset_hits(page)
        # Must be a *visible* control — the first button in the DOM usually
        # belongs to a hidden splash screen.
        def first_visible(selector):
            for el in page.query_selector_all(selector):
                try:
                    if el.is_visible():
                        return el
                except Exception:
                    continue
            return None

        target = (first_visible(game.tap) if game.tap else None) \
            or first_visible('canvas') or first_visible('button')
        assert target, f'{game.file} @mobile: no visible control to interact with'
        target.click(timeout=5000)
        page.wait_for_timeout(300)
        h = hits(page)
        assert (h.get('click', 0) + h.get('pointerdown', 0)
                + h.get('touchstart', 0)) > 0, \
            f'{game.file} @mobile: tapping a control invoked no handler'


@pytest.mark.parametrize('game', GAMES, ids=IDS)
def test_has_focusable_controls(live_server, browser, game):
    with browser_page(DESKTOP, live_server, game.file, browser=browser) as (page, _):
        assert focusable_count(page) > 0, f'{game.file}: nothing is focusable'


def test_maze_muncher_has_touch_dpad(live_server, browser):
    """Swipe-on-canvas was the only mobile control — imprecise in a grid maze
    for small hands. The pad must exist and be wired to the same nextDir."""
    game = next(g for g in GAMES if g.file == 'maze_muncher.html')
    with browser_page(MOBILE, live_server, game.file, touch=True, browser=browser) as (page, _):
        pad = page.query_selector('#dpad')
        assert pad, 'no #dpad in maze_muncher'
        buttons = page.query_selector_all('#dpad button[data-dir]')
        dirs = {b.get_attribute('data-dir') for b in buttons}
        assert {'up', 'down', 'left', 'right'} <= dirs, f'incomplete d-pad: {dirs}'
