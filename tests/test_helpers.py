"""Pure helpers in app.py."""

import pytest


def test_slugify_basic(app_module):
    assert app_module._slugify('Sort Bins!') == 'sort_bins'
    assert app_module._slugify('  Trains  ') == 'trains'
    assert app_module._slugify('a--b__c') == 'a_b_c'


def test_slugify_never_returns_empty(app_module):
    """Slugs become filenames/ids; empty would collide or crash downstream."""
    assert app_module._slugify('') == 'set'
    assert app_module._slugify('!!!') == 'set'
    assert app_module._slugify('日本語') == 'set'


def test_cache_image_passes_through_local_paths(app_module):
    """Already-cached paths must not be re-fetched (and with the network
    blocked, a regression here would surface as a hard failure)."""
    p = '/img-cache/abc123.jpg'
    assert app_module._cache_image(p) == p
    assert app_module._cache_image('') == ''


def test_cache_image_returns_original_url_on_failure(app_module, isolated_data):
    """Network is blocked by the autouse fixture, so this exercises the
    degradation path: a failed fetch returns the remote URL and the game
    falls back to loading it directly."""
    url = 'https://example.com/pic.jpg'
    assert app_module._cache_image(url) == url


@pytest.mark.parametrize('url,expected_ext', [
    ('https://x.com/a.jpeg', '.jpg'),
    ('https://x.com/a.png', '.png'),
    ('https://x.com/a.webp', '.webp'),
    ('https://x.com/a.gif', '.gif'),
    ('https://x.com/a', '.jpg'),
    ('https://x.com/a.PNG?w=100', '.png'),
])
def test_cache_image_extension_mapping(app_module, isolated_data, tmp_path,
                                       url, expected_ext, monkeypatch):
    """Extension is derived from the URL with the query string stripped;
    .jpeg normalises to .jpg. Verified via the filename it would write."""
    import hashlib
    import os
    h = hashlib.md5(url.encode()).hexdigest()
    target = os.path.join(str(tmp_path / 'img_cache'), h + expected_ext)
    # Pre-create the file so _cache_image short-circuits without fetching.
    open(target, 'wb').close()
    assert app_module._cache_image(url) == f'/img-cache/{h}{expected_ext}'


def _row(word, search, easy, hard):
    """_build_rounds consumes raw sqlite rows, indexing [2..5] —
    (id, lang, word, search, easy_json, hard_json)."""
    import json
    return (1, 'en', word, search, json.dumps(easy), json.dumps(hard))


@pytest.mark.parametrize('mode', ['easy', 'hard'])
def test_build_rounds_shape(app_module, isolated_data, mode):
    rows = [
        _row('cat', 'cat animal',
             [{'w': 'dog', 's': 'dog animal'}, {'w': 'sun', 's': 'sun sky'}],
             [{'w': 'bat', 's': 'bat animal'}, {'w': 'rat', 's': 'rat animal'}]),
        _row('bus', 'bus vehicle',
             [{'w': 'hat', 's': 'hat clothing'}, {'w': 'cup', 's': 'cup kitchen'}],
             [{'w': 'van', 's': 'van vehicle'}, {'w': 'car', 's': 'car vehicle'}]),
    ]
    rounds = app_module._build_rounds(rows, mode)
    assert len(rounds) == len(rows)
    for r in rounds:
        assert 'word' in r and 'choices' in r
        assert len(r['choices']) == 3, 'one target + two distractors'
        assert sum(1 for c in r['choices'] if c.get('correct')) == 1, \
            'each round must have exactly one correct choice'
        assert r['word'] in [c['word'] for c in r['choices']]


def test_build_rounds_picks_distractors_per_mode(app_module, isolated_data):
    """easy and hard pull from different distractor pools — a swap here would
    silently make every round the wrong difficulty."""
    rows = [_row('cat', 'cat animal',
                 [{'w': 'EASYONE', 's': 'a'}, {'w': 'EASYTWO', 's': 'b'}],
                 [{'w': 'HARDONE', 's': 'c'}, {'w': 'HARDTWO', 's': 'd'}])]
    easy_words = {c['word'] for c in app_module._build_rounds(rows, 'easy')[0]['choices']}
    hard_words = {c['word'] for c in app_module._build_rounds(rows, 'hard')[0]['choices']}
    assert 'EASYONE' in easy_words and 'HARDONE' not in easy_words
    assert 'HARDONE' in hard_words and 'EASYONE' not in hard_words
