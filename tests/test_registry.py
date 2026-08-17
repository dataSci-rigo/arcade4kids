"""GAMES registry integrity.

GAMES is both the hub's content and the /games/ allowlist (_ALLOWED is derived
from it), so a malformed entry either breaks a card or makes a game
unreachable. It's also where orphans show up: arcade.html sat in the repo
unregistered, 404ing on every request, with nothing to catch it.
"""

import glob
import os
import re

import pytest

from baseline import ALL_PLAYABLE, KNOWN_ORPHANS, TIER_ADMIN
from conftest import REPO

REQUIRED = ('key', 'title', 'desc', 'desktop', 'mobile', 'color', 'stripe')


def test_required_fields_present(app_module):
    for g in app_module.GAMES:
        missing = [f for f in REQUIRED if f not in g]
        assert not missing, f'{g.get("key", g)} missing {missing}'


def test_keys_are_unique(app_module):
    keys = [g['key'] for g in app_module.GAMES]
    dupes = {k for k in keys if keys.count(k) > 1}
    assert not dupes, f'duplicate GAMES keys: {dupes}'


def test_referenced_files_exist(app_module):
    for g in app_module.GAMES:
        for slot in ('desktop', 'mobile'):
            path = os.path.join(REPO, g[slot])
            assert os.path.isfile(path), f'{g["key"]}.{slot} -> {g[slot]} not on disk'


def test_colors_are_hex(app_module):
    for g in app_module.GAMES:
        assert re.fullmatch(r'#[0-9a-fA-F]{6}', g['color']), \
            f'{g["key"]} color {g["color"]!r} is not a 6-digit hex'


def test_desc_is_two_lines(app_module):
    """The hub card layout assumes exactly two lines."""
    for g in app_module.GAMES:
        assert isinstance(g['desc'], list) and len(g['desc']) == 2, \
            f'{g["key"]} desc must be a 2-element list, got {g["desc"]!r}'


def test_no_unregistered_html_files(app_module):
    """Catches the arcade.html class of bug: a game file in the repo that
    nothing can reach because it was never added to GAMES."""
    on_disk = {os.path.basename(p) for p in glob.glob(os.path.join(REPO, '*.html'))}
    registered = {g['desktop'] for g in app_module.GAMES} | \
                 {g['mobile'] for g in app_module.GAMES}
    orphans = on_disk - registered - KNOWN_ORPHANS
    assert not orphans, (
        f'unregistered .html files (unreachable via /games/): {sorted(orphans)}. '
        'Register them in GAMES or add to KNOWN_ORPHANS in baseline.py.'
    )


def test_baseline_matches_registry(app_module):
    """baseline.py's tier map must not drift from the real registry."""
    registered = {g['desktop'] for g in app_module.GAMES}
    known = ALL_PLAYABLE | TIER_ADMIN
    assert registered == known, (
        f'baseline.py out of sync with GAMES.\n'
        f'  in GAMES only:    {sorted(registered - known)}\n'
        f'  in baseline only: {sorted(known - registered)}'
    )
