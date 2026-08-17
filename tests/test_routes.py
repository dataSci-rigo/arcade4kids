"""File-serving route guards.

app.py hand-rolls a regex guard per route instead of using one helper, so each
has drifted independently — which is exactly how the phoneme bug happened.
These tests pin every guard's accept/reject behaviour so the next edit to one
of them can't silently narrow what a game is allowed to load.
"""

import pytest

# (route prefix, a path that must be rejected)
TRAVERSAL = [
    '../app.py',
    '../.env',
    '../../etc/passwd',
    'phonemes/../../app.py',
    '..%2Fapp.py',
    '/etc/passwd',
]

FILE_ROUTES = ['/audio/', '/images/', '/img-cache/', '/games/']


@pytest.mark.parametrize('prefix', FILE_ROUTES)
@pytest.mark.parametrize('evil', TRAVERSAL)
def test_traversal_is_rejected(client, prefix, evil):
    resp = client.get(f'{prefix}{evil}')
    assert resp.status_code in (400, 404, 308), (
        f'{prefix}{evil} returned {resp.status_code} — path traversal may be possible'
    )


def test_serve_game_is_allowlist_based(client, app_module):
    """Unlike the others, /games/ checks membership in _ALLOWED rather than a
    regex — an unregistered file must not be servable even if it exists."""
    for f in app_module._ALLOWED:
        assert client.get(f'/games/{f}').status_code == 200, f'{f} should serve'
    assert client.get('/games/app.py').status_code == 404
    assert client.get('/games/nope.html').status_code == 404


def test_audio_guard_accepts_phonemes_subdir(client):
    """Locks the fix. The original guard had no '/' and no A-Z, so every
    phoneme 404'd. Regex-level assertion so it fails even without audio/."""
    import re
    import app
    src = open(app.__file__).read()
    m = re.search(r"def serve_audio.*?re\.fullmatch\(r'([^']+)'", src, re.S)
    assert m, 'could not locate serve_audio guard'
    pattern = m.group(1)
    assert re.fullmatch(pattern, 'phonemes/SH.mp3'), (
        f'guard {pattern!r} rejects phonemes/SH.mp3 — Sound Speller is broken'
    )
    assert re.fullmatch(pattern, 'count_it_prompt.mp3')
    assert not re.fullmatch(pattern, '../secret.mp3')


def test_hub_renders_every_registered_game(client, app_module):
    body = client.get('/').get_data(as_text=True)
    missing = [g['title'] for g in app_module.GAMES if g['title'] not in body]
    assert not missing, f'hub is missing cards for: {missing}'


def test_unknown_paths_404(client):
    assert client.get('/definitely-not-a-route').status_code == 404
