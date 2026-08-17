"""Shared fixtures.

Three safety rules govern this suite, in priority order:

1. NEVER mutate real data. custom_sets.json, settings.json and vocab.db were
   recovered from a flash-drive backup and are not reproducible. Any test that
   writes must use the `isolated_data` fixture. `data_files_unchanged` is an
   autouse session guard that hashes them and fails the run if anything moved.

2. NEVER touch the network. `no_network` (autouse) makes urllib raise, so no
   test can reach DuckDuckGo or Unsplash. Routes needing images must mock
   app._ddg_images / _ddg_image / _cache_image.

3. NEVER make a billable API call. `no_anthropic` (autouse) replaces the
   anthropic.Anthropic class with a stub. Note app.py imports anthropic
   *inside* functions (app.py:1179, 1314, 1563), so the class is patched on the
   module object rather than in app's namespace.

Known import-time side effect: app.py calls _vocab_init() and
_seed_vocab_base() at module scope (app.py:690-691) against the real vocab.db.
It is idempotent (INSERT OR IGNORE) so it is safe and intentional — do not
"fix" it by pointing tests at a temp DB and wondering why seeding still fires.
The path constants are only rebindable *after* import.
"""

import hashlib
import os
import shutil
import sys
import threading
import urllib.request

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import app as arcade_app  # noqa: E402  (after sys.path fix)

# Data files that must survive the suite untouched.
PROTECTED = ['custom_sets.json', 'settings.json', 'vocab.db', 'letter_words.json']


def _digest(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture(scope='session', autouse=True)
def data_files_unchanged():
    """Fail loudly if any test mutated irreplaceable data."""
    before = {n: _digest(os.path.join(REPO, n)) for n in PROTECTED}
    yield
    after = {n: _digest(os.path.join(REPO, n)) for n in PROTECTED}
    changed = [n for n in PROTECTED if before[n] != after[n]]
    assert not changed, (
        f'Test run mutated protected data files: {changed}. '
        'A test wrote to real data instead of using the isolated_data fixture.'
    )


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Any real outbound request is a bug in the test, not a flake.

    Patches urlopen only — every outbound call in app.py goes through it
    (_ddg_images, _cache_image, tts). Deliberately NOT patching
    socket.connect: that would also sever Playwright's link to Chromium and
    the loopback connection to the live server fixture.
    """
    def _blocked(*a, **k):
        raise AssertionError(
            'Test attempted a real network request. Mock _ddg_images/_cache_image.'
        )
    monkeypatch.setattr(urllib.request, 'urlopen', _blocked)


@pytest.fixture(autouse=True)
def no_anthropic(monkeypatch):
    """Hard stop on billable API calls."""
    try:
        import anthropic
    except ImportError:
        return
    class _Blocked:
        def __init__(self, *a, **k):
            raise AssertionError('Test attempted a real Anthropic API call.')
    monkeypatch.setattr(anthropic, 'Anthropic', _Blocked)


@pytest.fixture
def isolated_data(tmp_path, monkeypatch):
    """Redirect all persistence at a throwaway copy.

    app.py reads these globals at call time inside each route, so rebinding
    them on the module is enough — no reimport needed.
    """
    for name in ('custom_sets.json', 'settings.json', 'vocab.db'):
        src = os.path.join(REPO, name)
        if os.path.exists(src):
            shutil.copy2(src, tmp_path / name)

    cache = tmp_path / 'img_cache'
    cache.mkdir()

    monkeypatch.setattr(arcade_app, 'CUSTOM_SETS_FILE', str(tmp_path / 'custom_sets.json'))
    monkeypatch.setattr(arcade_app, 'SETTINGS_FILE', str(tmp_path / 'settings.json'))
    monkeypatch.setattr(arcade_app, 'VOCAB_DB', str(tmp_path / 'vocab.db'))
    monkeypatch.setattr(arcade_app, 'IMG_CACHE_DIR', str(cache))
    return tmp_path


@pytest.fixture
def client():
    arcade_app.app.config['TESTING'] = True
    with arcade_app.app.test_client() as c:
        yield c


@pytest.fixture(scope='session')
def app_module():
    return arcade_app


# ── Live server for the browser tiers ────────────────────────────────────────

@pytest.fixture(scope='session')
def browser():
    """One Chromium for the whole run.

    Launching per test cost ~15s each and made the browser tier a 35-minute
    job; contexts remain per-test so pages stay isolated.
    """
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    b = pw.chromium.launch()
    yield b
    b.close()
    pw.stop()


@pytest.fixture(scope='session')
def live_server():
    """Real socket on an ephemeral port — Playwright can't use test_client."""
    from werkzeug.serving import make_server

    arcade_app.app.config['TESTING'] = True
    srv = make_server('127.0.0.1', 0, arcade_app.app, threaded=True)
    port = srv.socket.getsockname()[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f'http://127.0.0.1:{port}'
    srv.shutdown()
    t.join(timeout=5)
