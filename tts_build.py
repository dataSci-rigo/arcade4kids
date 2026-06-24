"""
Generate pre-recorded "read aloud" audio clips for the kids games.

This is a dev-only build step — it is NOT run on the server. The resulting
mp3 files in audio/ are gitignored and get copied to the VM via scp by
deploy_arcade_model.sh, the same way models/emnist_letters.onnx is.

Run once locally, and again any time a new phrase is added below:
    conda run -n p312 python tts_build.py

Add --force to regenerate every clip even if the file already exists.
"""

import os
import sys

AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio')

# ── Shared phrases (US English, default voice) ────────────────────────────────
# id -> spoken text
PHRASES = {
    # Counting Garden
    'count_it_prompt': 'How many can you count?',
    'skip_by_1':        'Count by 1s!',
    'skip_by_2':        'Count by 2s!',
    'skip_by_3':        'Count by 3s!',
    'skip_by_4':        'Count by 4s!',
    'fill_it_prompt':   'Plant the flowers in the garden!',
    # Memory Match
    'player1_turn':     "Player 1's turn!",
    'player2_turn':     "Player 2's turn!",
}

# ── Math Smash: per-character clips ───────────────────────────────────────────
# Each non-Bolt character has a distinct gTTS accent via `tld`.
# Bolt uses Web Speech API at runtime (robotic voice), so no clips here.
MS_CHARS = {
    'zara': {
        'tld': 'co.uk', 'slow': False,
        'intros': [
            "Hi! I'm Zara! My magic wand once turned homework into candy!",
            "Hi! I'm Zara! I've been casting spells for 300 years and I still love it!",
            "Hi! I'm Zara! My pointed hat has a tiny dragon living inside it!",
        ],
        'prompt': "Please answer this for me!",
    },
    'rex': {
        'tld': 'com.au', 'slow': False,
        'intros': [
            "Hi! I'm Rex! I may be big, but I love learning new things every day!",
            "Hi! I'm Rex! My best friend is a tiny pterodactyl named Peep!",
            "Hi! I'm Rex! I've explored every continent at least twice!",
        ],
        'prompt': "Please answer this for me!",
    },
    'luna': {
        'tld': 'com', 'slow': False,
        'intros': [
            "Hi! I'm Luna! I've traveled to 42 different planets and counting!",
            "Hi! I'm Luna! My spaceship runs on stardust and good math skills!",
            "Hi! I'm Luna! I once high-fived an alien and we became best friends!",
        ],
        'prompt': "Please answer this for me!",
    },
    'finn': {
        'tld': 'co.uk', 'slow': False,  # closest to Scottish available in gTTS
        'intros': [
            "Hi! I'm Finn! I've sailed the seven seas looking for treasure!",
            "Hi! I'm Finn! My parrot Polly can solve math problems too!",
            "Hi! I'm Finn! I found twelve treasure chests just last Tuesday!",
        ],
        'prompt': "Please answer this for me!",
    },
    'lily': {
        'tld': 'ie', 'slow': False,
        'intros': [
            "Hi! I'm Lily! I can make flowers bloom just by sprinkling fairy dust!",
            "Hi! I'm Lily! My wings can fly around the world in under a minute!",
            "Hi! I'm Lily! I grant wishes to anyone who answers math questions!",
        ],
        'prompt': "Please answer this for me!",
    },
}

# ── Math Smash: scene descriptions (shared, US English) ───────────────────────
# Order must match the SCENES array in math_smash.html exactly.
MS_SCENES = [
    "I'm exploring this amazing underwater reef! The fish here are so colorful!",
    "I'm floating in outer space! Everything is completely weightless out here!",
    "I'm deep in an enchanted forest! Everything here glows with ancient magic!",
    "I'm inside a grand castle hall! The king himself invited me today!",
    "I'm in the most colorful meadow I've ever seen! Unicorns live here!",
    "I'm on a volcanic island! The lava is warm but I have a heat shield!",
    "I'm exploring the frozen arctic! The snow sparkles like a million diamonds!",
    "I found a beautiful oasis in the middle of the desert! Cool water at last!",
    "I live in the Cloud Kingdom! You can bounce on these clouds like trampolines!",
    "I live in a cozy mushroom village! The mushrooms are as big as houses here!",
    "I'm inside a magical crystal cave! Every wall sparkles like a rainbow!",
    "I discovered an ancient temple! This place is thousands of years old!",
    "I'm relaxing on a tropical beach! The sand is as soft as fluffy pillows!",
    "I climbed to the very top of this mountain! You can see the whole world up here!",
    "I'm walking through the autumn forest! The leaves crunch with every step!",
    "I'm at a magical night market! The lanterns light up the whole sky!",
    "I'm in the greatest magic library ever! Every single book in here can talk!",
    "I'm sailing on a pirate ship! We found a treasure map just this morning!",
    "I'm visiting my dragon friend! This dragon loves math even more than treasure!",
    "I'm in a city from the future! Everything here runs on math and electricity!",
]

# ── Math Smash: celebration messages (shared, US English) ─────────────────────
# Emoji stripped; order must match CELEB_MSGS in math_smash.html.
MS_CELEB = [
    "AMAZING! You got it!",
    "INCREDIBLE! So smart!",
    "PERFECT! You rock!",
    "BRILLIANT! High five!",
    "SPOT ON! You're a genius!",
    "OUT OF THIS WORLD!",
    "YOU'RE A MATH MASTER!",
    "UNBELIEVABLE!",
]


def main():
    try:
        from gtts import gTTS
    except ImportError:
        print("Installing gtts ...")
        os.system(f"{sys.executable} -m pip install gtts --quiet")
        from gtts import gTTS

    force = '--force' in sys.argv
    os.makedirs(AUDIO_DIR, exist_ok=True)

    def build(clip_id, text, tld='com', slow=False):
        out_path = os.path.join(AUDIO_DIR, f"{clip_id}.mp3")
        if os.path.exists(out_path) and not force:
            print(f"  skip  {clip_id}.mp3")
            return
        gTTS(text=text, lang='en', tld=tld, slow=slow).save(out_path)
        print(f"  built {clip_id}.mp3  [{tld}]  ({text[:60]!r}{'...' if len(text)>60 else ''})")

    # Shared phrases (existing games)
    print("\n── Shared (Counting Garden & Memory Match) ──")
    for clip_id, text in PHRASES.items():
        build(clip_id, text)

    # Math Smash — per-character intro + prompt clips
    print("\n── Math Smash: character clips ──")
    for char_key, cfg in MS_CHARS.items():
        for i, intro in enumerate(cfg['intros']):
            build(f"ms_{char_key}_intro_{i}", intro, tld=cfg['tld'], slow=cfg['slow'])
        build(f"ms_{char_key}_prompt", cfg['prompt'], tld=cfg['tld'], slow=cfg['slow'])

    # Math Smash — shared scene narrations
    print("\n── Math Smash: scene clips ──")
    for i, txt in enumerate(MS_SCENES):
        build(f"ms_scene_{i}", txt)

    # Math Smash — shared celebration messages
    print("\n── Math Smash: celebration clips ──")
    for i, txt in enumerate(MS_CELEB):
        build(f"ms_celeb_{i}", txt)

    print(f"\nDone. Clips in {AUDIO_DIR}")


if __name__ == '__main__':
    main()
