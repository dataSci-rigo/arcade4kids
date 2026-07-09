"""
Generate pre-recorded "read aloud" audio clips for the kids games.

This is a dev-only build step — it is NOT run on the server. The resulting
mp3 files in audio/ are gitignored and get copied to the VM via scp by
deploy_arcade_model.sh, the same way models/emnist_letters.onnx is.

Run once locally, and again any time a new phrase is added below:
    conda run -n p314 python tts_build.py

Add --force to regenerate every clip even if the file already exists.

Voices used (edge-tts):
  Shared / celebrations : en-US-JennyNeural   (American female)
  Zara (wizard)         : en-GB-SoniaNeural   (British female)
  Rex  (dino)           : en-AU-WilliamMultilingualNeural (Australian male)
  Luna (astronaut)      : en-US-AvaNeural     (American female)
  Finn (pirate)         : en-GB-RyanNeural    (British male)
  Lily (fairy)          : en-IE-EmilyNeural   (Irish female)
  Bolt (robot)          : Web Speech API at runtime — no clips here
"""

import os
import sys
import asyncio

AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio')

SHARED_VOICE = 'en-US-JennyNeural'

# ── Shared phrases (US English) ───────────────────────────────────────────────
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
# Bolt uses Web Speech API at runtime (robotic voice), so no clips here.
MS_CHARS = {
    'zara': {
        'voice': 'en-GB-SoniaNeural',   # British female
        'intros': [
            "Hi! I'm Zara! My magic wand once turned homework into candy!",
            "Hi! I'm Zara! I've been casting spells for 300 years and I still love it!",
            "Hi! I'm Zara! My pointed hat has a tiny dragon living inside it!",
        ],
        'prompt': "Please answer this for me!",
    },
    'rex': {
        'voice': 'en-AU-WilliamMultilingualNeural',  # Australian male
        'intros': [
            "Hi! I'm Rex! I may be big, but I love learning new things every day!",
            "Hi! I'm Rex! My best friend is a tiny pterodactyl named Peep!",
            "Hi! I'm Rex! I've explored every continent at least twice!",
        ],
        'prompt': "Please answer this for me!",
    },
    'luna': {
        'voice': 'en-US-AvaNeural',     # American female
        'intros': [
            "Hi! I'm Luna! I've traveled to 42 different planets and counting!",
            "Hi! I'm Luna! My spaceship runs on stardust and good math skills!",
            "Hi! I'm Luna! I once high-fived an alien and we became best friends!",
        ],
        'prompt': "Please answer this for me!",
    },
    'finn': {
        'voice': 'en-GB-RyanNeural',    # British male (closest to Scottish in edge-tts)
        'intros': [
            "Hi! I'm Finn! I've sailed the seven seas looking for treasure!",
            "Hi! I'm Finn! My parrot Polly can solve math problems too!",
            "Hi! I'm Finn! I found twelve treasure chests just last Tuesday!",
        ],
        'prompt': "Please answer this for me!",
    },
    'lily': {
        'voice': 'en-IE-EmilyNeural',   # Irish female
        'intros': [
            "Hi! I'm Lily! I can make flowers bloom just by sprinkling fairy dust!",
            "Hi! I'm Lily! My wings can fly around the world in under a minute!",
            "Hi! I'm Lily! I grant wishes to anyone who answers math questions!",
        ],
        'prompt': "Please answer this for me!",
    },
}

# ── Math Smash: scene descriptions ────────────────────────────────────────────
# One clip per character per scene (ms_scene_{i}_{charkey}.mp3) so the
# accent stays consistent with the character speaking in bubbles 1 and 3.
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


async def build(clip_id, text, voice, force=False):
    import edge_tts
    out_path = os.path.join(AUDIO_DIR, f"{clip_id}.mp3")
    if os.path.exists(out_path) and not force:
        print(f"  skip  {clip_id}.mp3")
        return
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_path)
    print(f"  built {clip_id}.mp3  [{voice}]  ({text[:60]!r}{'...' if len(text)>60 else ''})")


async def amain(force):
    os.makedirs(AUDIO_DIR, exist_ok=True)

    # Shared phrases
    print("\n── Shared (Counting Garden & Memory Match) ──")
    tasks = [build(cid, txt, SHARED_VOICE, force) for cid, txt in PHRASES.items()]
    await asyncio.gather(*tasks)

    # Math Smash — per-character intro + prompt clips
    print("\n── Math Smash: character clips ──")
    tasks = []
    for char_key, cfg in MS_CHARS.items():
        for i, intro in enumerate(cfg['intros']):
            tasks.append(build(f"ms_{char_key}_intro_{i}", intro, cfg['voice'], force))
        tasks.append(build(f"ms_{char_key}_prompt", cfg['prompt'], cfg['voice'], force))
    await asyncio.gather(*tasks)

    # Math Smash — per-character scene clips
    print("\n── Math Smash: scene clips (per character) ──")
    tasks = []
    for char_key, cfg in MS_CHARS.items():
        for i, txt in enumerate(MS_SCENES):
            tasks.append(build(f"ms_scene_{i}_{char_key}", txt, cfg['voice'], force))
    await asyncio.gather(*tasks)

    # Math Smash — celebration messages
    print("\n── Math Smash: celebration clips ──")
    tasks = [build(f"ms_celeb_{i}", txt, SHARED_VOICE, force) for i, txt in enumerate(MS_CELEB)]
    await asyncio.gather(*tasks)

    print(f"\nDone. Clips in {AUDIO_DIR}")


def main():
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        print("edge-tts not found. Install it with:  pip install edge-tts")
        sys.exit(1)

    force = '--force' in sys.argv
    asyncio.run(amain(force))


if __name__ == '__main__':
    main()
