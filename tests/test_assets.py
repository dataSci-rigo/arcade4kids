"""Every asset a game asks for must actually resolve through its route.

This is the tier that exists because of a real, shipped bug: serve_audio's
guard was `[a-z0-9_]+\\.mp3`, which rejected both the '/' and the uppercase
digraph names in /audio/phonemes/SH.mp3. All 43 phoneme clips 404'd in
committed HEAD and Sound Speller's core mechanic was silently dead.

The lesson generalised: it is not enough for a file to exist on disk, and not
enough for a route to look sane. The URL a game actually requests must survive
the guard and return bytes. So we walk the real filesystem and assert exactly
that, for every asset, rather than spot-checking a few.
"""

import os

import pytest

from baseline import AUDIO_EXCLUDE_PREFIXES, CLIP_FAMILIES
from conftest import REPO

AUDIO_DIR = os.path.join(REPO, 'audio')
IMAGES_DIR = os.path.join(REPO, 'images')
IMG_CACHE_DIR = os.path.join(REPO, 'img_cache')


def _rel_mp3s():
    """Every mp3 under audio/, as the URL path a game would request."""
    out = []
    for root, _dirs, files in os.walk(AUDIO_DIR):
        for f in sorted(files):
            if not f.endswith('.mp3'):
                continue
            if f.startswith(AUDIO_EXCLUDE_PREFIXES):
                continue
            out.append(os.path.relpath(os.path.join(root, f), AUDIO_DIR))
    return out


@pytest.mark.skipif(not os.path.isdir(AUDIO_DIR), reason='audio/ not restored')
@pytest.mark.parametrize('rel', _rel_mp3s())
def test_every_audio_file_is_reachable(client, rel):
    """Regression lock for the phoneme 404.

    Covers all 217 clips including the 43 in audio/phonemes/ whose uppercase
    digraph names (SH, TH, NG, OA...) the original guard rejected.
    """
    resp = client.get(f'/audio/{rel}')
    assert resp.status_code == 200, f'/audio/{rel} unreachable ({resp.status_code})'
    assert len(resp.data) > 0


@pytest.mark.skipif(not os.path.isdir(AUDIO_DIR), reason='audio/ not restored')
def test_phoneme_clips_present_and_served(client):
    """Sound Speller needs its phoneme set specifically — assert as a group."""
    ph_dir = os.path.join(AUDIO_DIR, 'phonemes')
    assert os.path.isdir(ph_dir), 'audio/phonemes/ missing'
    names = [f for f in os.listdir(ph_dir) if f.endswith('.mp3')]
    assert len(names) >= 40, f'expected the full phoneme set, found {len(names)}'
    unreachable = [n for n in names
                   if client.get(f'/audio/phonemes/{n}').status_code != 200]
    assert not unreachable, f'phonemes unreachable: {sorted(unreachable)}'


@pytest.mark.skipif(not os.path.isdir(AUDIO_DIR), reason='audio/ not restored')
@pytest.mark.parametrize('family', sorted(CLIP_FAMILIES))
def test_clip_families_have_no_gaps(client, family):
    """Games build clip ids from template literals; a missing member is a
    silent dead sound mid-game, so expand the family and check every member."""
    missing = []
    for clip in CLIP_FAMILIES[family]:
        if client.get(f'/audio/{clip}.mp3').status_code != 200:
            missing.append(clip)
    assert not missing, f'{family}: {len(missing)} missing, e.g. {missing[:5]}'


@pytest.mark.skipif(not os.path.isdir(IMAGES_DIR), reason='images/ not restored')
@pytest.mark.parametrize('name', sorted(os.listdir(IMAGES_DIR))
                         if os.path.isdir(IMAGES_DIR) else [])
def test_every_image_is_reachable(client, name):
    assert client.get(f'/images/{name}').status_code == 200


@pytest.mark.skipif(not os.path.isdir(os.path.join(IMG_CACHE_DIR, 'math_smash')),
                    reason='math_smash scene cache not fetched')
def test_math_smash_scenes_complete(client):
    """math_smash.html:702 maps 20 Unsplash ids to /img-cache/math_smash/scene_N.jpg
    and falls back to the remote URL on a miss — so gaps degrade to a network
    dependency rather than an error. Assert the local cache is whole."""
    missing = [i for i in range(20)
               if client.get(f'/img-cache/math_smash/scene_{i}.jpg').status_code != 200]
    assert not missing, f'scene images missing: {missing}'
