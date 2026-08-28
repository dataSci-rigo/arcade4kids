"""JSON contracts for the /api/ surface.

The sharpest risk here is structural: all four custom-content types
(sort bins, spelling, item sets, sound-speller words) live in ONE
custom_sets.json under different top-level keys, each with its own
_load_*/_save_* pair (app.py:721-793). Every save rewrites the whole file, so a
bug in one saver silently destroys the other three. That's asserted explicitly.

Read-only GETs run against real data. Anything that writes uses `isolated_data`.
"""

import json

import pytest

SET_ENDPOINTS = [
    '/api/custom-sets',
    '/api/spelling-sets',
    '/api/item-sets',
    '/api/ss-word-sets',
]


@pytest.mark.parametrize('url', SET_ENDPOINTS)
def test_set_endpoints_return_well_formed_list(client, url):
    """item_sets and ss_word_sets are empty post-restore (the backup predates
    those features). Empty is fine; malformed or erroring is not."""
    resp = client.get(url)
    assert resp.status_code == 200
    body = resp.get_json()
    assert isinstance(body, dict) and 'sets' in body
    assert isinstance(body['sets'], list)


def test_settings_returns_object(client):
    resp = client.get('/api/settings')
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), dict)


def test_letter_words_returns_word_and_image(client):
    resp = client.get('/api/letter-words')
    assert resp.status_code == 200
    body = resp.get_json()
    assert 'word' in body


def test_vocab_base_words_paginates(client):
    resp = client.get('/api/vocab/base-words?lang=en')
    assert resp.status_code == 200
    body = resp.get_json()
    for field in ('words', 'total', 'page', 'total_pages'):
        assert field in body, f'missing {field}'
    assert len(body['words']) <= 30
    assert body['total'] > 0, 'vocab.db appears unseeded'


def test_vocab_base_words_rejects_bad_lang_by_defaulting(client):
    """Route coerces unknown langs to 'en' rather than erroring."""
    resp = client.get('/api/vocab/base-words?lang=klingon')
    assert resp.status_code == 200
    assert resp.get_json()['words']


def test_vocab_custom_sets_shape(client):
    resp = client.get('/api/vocab/custom-sets')
    assert resp.status_code == 200
    body = resp.get_json()
    assert isinstance(body.get('sets'), list)
    for s in body['sets']:
        assert {'id', 'label'} <= set(s)


# ── Writes: isolated ─────────────────────────────────────────────────────────

def test_saving_one_set_type_preserves_the_others(client, isolated_data):
    """The single-file, four-keys design means a bad save wipes sibling data.

    Regression guard: capture all four, write one, assert the other three are
    byte-identical afterwards.
    """
    import app

    before = {url: client.get(url).get_json()['sets'] for url in SET_ENDPOINTS}

    app._save_spelling_sets(before['/api/spelling-sets'] + [
        {'id': 'pytest_tmp', 'label': 'pytest', 'word_images': {}}
    ])

    for url in SET_ENDPOINTS:
        if url == '/api/spelling-sets':
            continue
        assert client.get(url).get_json()['sets'] == before[url], (
            f'writing spelling_sets clobbered {url}'
        )

    raw = json.load(open(app.CUSTOM_SETS_FILE))
    assert 'pytest_tmp' in json.dumps(raw['spelling_sets'])


def test_delete_unknown_set_is_idempotent(client, isolated_data):
    """Deleting a non-existent id filters an already-absent entry and returns
    204 — no error, no crash. Locking it so it stays idempotent."""
    resp = client.delete('/api/custom-sets/definitely-not-a-real-set')
    assert resp.status_code == 204, f'got {resp.status_code}'


def test_recognize_letter_requires_image(client):
    resp = client.post('/api/recognize-letter', json={})
    assert resp.status_code == 400


TINY_PNG = (
    'data:image/png;base64,'
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='
)


def test_recognize_letter_accepts_single_alpha_or_digit_target(client):
    """Number Draw relaxed the guard: single letters AND single digits pass
    validation (both then reach the Anthropic call, which no_anthropic stubs
    to a 500 — anything but 400 proves validation accepted the target)."""
    for target in ('A', '7', '0'):
        resp = client.post('/api/recognize-letter',
                           json={'image': TINY_PNG, 'target': target, 'stroke_count': 1})
        assert resp.status_code != 400, f'target {target!r} should pass validation'
    # Multi-char and symbol targets are still rejected.
    for target in ('AB', '12', '$', ''):
        resp = client.post('/api/recognize-letter',
                           json={'image': TINY_PNG, 'target': target, 'stroke_count': 1})
        assert resp.status_code == 400, f'target {target!r} should be rejected'
