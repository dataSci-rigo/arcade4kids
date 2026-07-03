"""
Generate pre-recorded phoneme audio clips for Sound Speller.

Run once (or with --force to regenerate):
    /home/ai1/anaconda3/envs/p312/bin/python3 generate_phonemes.py

Output: audio/phonemes/<PHONEME>.mp3
"""

import os
import sys

AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio', 'phonemes')

# Map internal phoneme codes → (gTTS text, tld, slow)
# Strategy:
#   Vowels       → phonetic spellings gTTS reads naturally
#   Continuants  → stretched spellings ("sss", "mmm") so the pure sound comes through
#   Stops        → "Xuh" syllable (industry-standard phonics isolation)
#   Digraphs     → syllables chosen so gTTS doesn't spell out the letters
PHONEMES = {
    # ── Short vowels ──────────────────────────────────────────────────────────
    'a':  ('apple',       'com', True),   # /æ/  — key-word approach; listener hears onset
    'e':  ('echo',        'com', True),   # /ɛ/
    'i':  ('itch',        'com', True),   # /ɪ/
    'o':  ('on',          'com', True),   # /ɒ/
    'u':  ('up',          'com', True),   # /ʌ/

    # ── Long vowels / vowel teams ─────────────────────────────────────────────
    'AI': ('ay',          'com', True),   # /eɪ/
    'EE': ('ee',          'com', True),   # /iː/
    'IE': ('eye',         'com', True),   # /aɪ/
    'OA': ('owe',         'com', True),   # /oʊ/
    'UE': ('oo',          'com', True),   # /uː/
    'OO': ('oo',          'com', True),   # /ʊ/ (book-vowel; same clip as UE, context differs)

    # ── Diphthongs ────────────────────────────────────────────────────────────
    'OW': ('ow',          'com', True),   # /aʊ/ — "ow" as in ouch
    'OY': ('oy',          'com', True),   # /ɔɪ/

    # ── R-controlled vowels ───────────────────────────────────────────────────
    'AR': ('ar',          'com', True),   # /ɑːr/
    'OR': ('or',          'com', True),   # /ɔːr/
    'ER': ('er',          'com', True),   # /ɜːr/

    # ── Stops ─────────────────────────────────────────────────────────────────
    'b':  ('buh',         'com', True),
    'd':  ('duh',         'com', True),
    'g':  ('guh',         'com', True),
    'k':  ('kuh',         'com', True),
    'p':  ('puh',         'com', True),
    't':  ('tuh',         'com', True),

    # ── Fricatives / continuants ──────────────────────────────────────────────
    'f':  ('fff',         'com', True),
    'h':  ('huh',         'com', True),
    'l':  ('lll',         'com', True),
    'm':  ('mmm',         'com', True),
    'n':  ('nnn',         'com', True),
    'r':  ('rrr',         'com', True),
    's':  ('sss',         'com', True),
    'v':  ('vvv',         'com', True),
    'w':  ('wuh',         'com', True),
    'x':  ('ks',          'com', True),   # /ks/
    'y':  ('yuh',         'com', True),
    'z':  ('zzz',         'com', True),
    'j':  ('juh',         'com', True),
    'c':  ('kuh',         'com', True),   # same as k

    # ── Digraphs ──────────────────────────────────────────────────────────────
    'SH': ('shhhh',       'com', True),   # /ʃ/
    'CH': ('chuh',        'com', True),   # /tʃ/
    'TH': ('think',       'com', True),   # /θ/ voiceless — key-word approach
    'DH': ('the',         'com', True),   # /ð/ voiced
    'NG': ('nng',         'com', True),   # /ŋ/
    'WH': ('wuh',         'com', True),   # /w/ (standard American)

    # ── Other ─────────────────────────────────────────────────────────────────
    'qu': ('kwuh',        'com', True),
}


def main():
    from gtts import gTTS

    force = '--force' in sys.argv
    os.makedirs(AUDIO_DIR, exist_ok=True)

    built = skipped = 0
    for code, (text, tld, slow) in PHONEMES.items():
        out = os.path.join(AUDIO_DIR, f'{code}.mp3')
        if os.path.exists(out) and not force:
            print(f'  skip   {code}.mp3')
            skipped += 1
            continue
        try:
            gTTS(text=text, lang='en', tld=tld, slow=slow).save(out)
            print(f'  built  {code}.mp3  ({text!r})')
            built += 1
        except Exception as e:
            print(f'  ERROR  {code}.mp3: {e}')

    print(f'\nDone — {built} built, {skipped} skipped. Files in:\n  {AUDIO_DIR}')


if __name__ == '__main__':
    main()
