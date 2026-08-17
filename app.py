import json
import os
import io
import base64
import re
import random
import hashlib
import sqlite3
import urllib.request
import urllib.parse
from flask import Flask, render_template, send_from_directory, abort, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, 'settings.json')
CUSTOM_SETS_FILE = os.path.join(BASE_DIR, 'custom_sets.json')
VOCAB_DB = os.path.join(BASE_DIR, 'vocab.db')
IMG_CACHE_DIR = os.path.join(BASE_DIR, 'img_cache')
os.makedirs(IMG_CACHE_DIR, exist_ok=True)

GAMES = [
    {
        'key':      'racer',
        'title':    'ENDLESS RUNNER',
        'desc':     ['3 THEMES · DODGE OBSTACLES', 'SURVIVE THE TUNNEL'],
        'desktop':  'racer.html',
        'mobile':   'racer.html',
        'color':    '#44ee44',
        'stripe':   'linear-gradient(90deg,#33cc33,#ffdd00)',
    },
    {
        'key':      'maze',
        'title':    'MAZE MUNCHER',
        'desc':     ['EAT DOTS · BEAT THE CLOCK', 'FIND THE EXIT'],
        'desktop':  'maze_muncher.html',
        'mobile':   'maze_muncher.html',
        'color':    '#00ccff',
        'stripe':   'linear-gradient(90deg,#0066ff,#00ccff)',
    },
    {
        'key':      'math_smash',
        'title':    'MATH SMASH',
        'desc':     ['SOLVE FAST · SMASH NUMBERS', 'BEAT THE CLOCK'],
        'desktop':  'math_smash.html',
        'mobile':   'math_smash.html',
        'color':    '#4ECDC4',
        'stripe':   'linear-gradient(90deg,#4ECDC4,#FFE66D)',
    },
    {
        'key':      'big_green',
        'title':    'BIG GREEN',
        'desc':     ['8-BIT PLATFORMER · JUMP & RUN', 'STOMP YOUR ENEMIES'],
        'desktop':  'big_green.html',
        'mobile':   'big_green.html',
        'color':    '#44ff88',
        'stripe':   'linear-gradient(90deg,#44ff88,#00cc44)',
    },
    {
        'key':      'letter_draw',
        'title':    'LETTER DRAW',
        'desc':     ['TRACE LETTERS · LEARN THE ABC', 'PHONE ONLY'],
        'desktop':  'letter_draw.html',
        'mobile':   'letter_draw.html',
        'color':    '#FF6B9D',
        'stripe':   'linear-gradient(90deg,#FF6B9D,#FFE66D)',
    },
    {
        'key':      'spelling_adventure',
        'title':    'SPELLING ADVENTURE',
        'desc':     ['SPOT THE IMAGE · SPELL THE WORD', 'POWERED BY DUCKDUCKGO'],
        'desktop':  'spelling_adventure.html',
        'mobile':   'spelling_adventure.html',
        'color':    '#c77dff',
        'stripe':   'linear-gradient(90deg,#667eea,#c77dff)',
    },
    {
        'key':      'memory_match',
        'title':    'MEMORY MATCH',
        'desc':     ['FLIP & MATCH · 1 OR 2 PLAYERS', 'FIND THE PAIRS'],
        'desktop':  'memory_match.html',
        'mobile':   'memory_match.html',
        'color':    '#FF6B9D',
        'stripe':   'linear-gradient(90deg,#FF6B9D,#4ECDC4)',
    },
    {
        'key':      'counting_game',
        'title':    'COUNTING GARDEN',
        'desc':     ['COUNT BY 1s 2s 3s 4s', 'GROW YOUR GARDEN'],
        'desktop':  'counting_game.html',
        'mobile':   'counting_game.html',
        'color':    '#A8E6CF',
        'stripe':   'linear-gradient(90deg,#A8E6CF,#FFE66D)',
    },
    {
        'key':      'math_garden',
        'title':    'MATH GARDEN',
        'desc':     ['COUNT · ADD · SUBTRACT', 'GROW YOUR EQUATIONS'],
        'desktop':  'math_garden.html',
        'mobile':   'math_garden.html',
        'color':    '#6366f1',
        'stripe':   'linear-gradient(90deg,#6366f1,#4ECDC4)',
    },
    {
        'key':      'sort_game',
        'title':    'SORT IT OUT',
        'desc':     ['DRAG TO THE RIGHT BIN', 'ANIMALS · FOOD · VEHICLES'],
        'desktop':  'sort_game.html',
        'mobile':   'sort_game.html',
        'color':    '#FFE66D',
        'stripe':   'linear-gradient(90deg,#FFE66D,#FF6B6B)',
    },
    {
        'key':      'shape_shift',
        'title':    'SHAPE SHIFT',
        'desc':     ['ROTATE · FLIP · BIGGER · SMALLER', 'FIND THE MATCH'],
        'desktop':  'shape_shift.html',
        'mobile':   'shape_shift.html',
        'color':    '#f97316',
        'stripe':   'linear-gradient(90deg,#f97316,#fbbf24)',
    },
    {
        'key':      'vocab_builder',
        'title':    'VOCAB BUILDER',
        'desc':     ['MATCH THE WORD · LEARN FAST', 'EN · ES · AI LEVELS'],
        'desktop':  'vocab_builder.html',
        'mobile':   'vocab_builder.html',
        'color':    '#FF6B9D',
        'stripe':   'linear-gradient(90deg,#FF6B9D,#c77dff)',
    },
    {
        'key':      'sort_builder',
        'title':    'CUSTOM ITEMS BUILDER',
        'desc':     ['IMAGES FOR ALL GAMES', 'SORT · COUNT · MATH · VOCAB'],
        'desktop':  'sort_set_builder.html',
        'mobile':   'sort_set_builder.html',
        'color':    '#9B59B6',
        'stripe':   'linear-gradient(90deg,#9B59B6,#FFE66D)',
    },
    {
        'key':      'sound_speller',
        'title':    'SOUND SPELLER',
        'desc':     ['HEAR IT · BUILD IT', '6 PHONICS LEVELS'],
        'desktop':  'sound_speller.html',
        'mobile':   'sound_speller.html',
        'color':    '#FF8A5B',
        'stripe':   'linear-gradient(90deg,#5B5BD6,#FF8A5B)',
    },
    {
        'key':      'pip_bear',
        'title':    'PIP THE BEAR',
        'desc':     ['A PICTURE BOOK ADVENTURE', '7 PAGES · MATH QUESTIONS'],
        'desktop':  'pip_the_bear.html',
        'mobile':   'pip_the_bear.html',
        'color':    '#8B5A2B',
        'stripe':   'linear-gradient(90deg,#2a3f5f,#5e4b8e)',
    },
]

# Only files explicitly registered above can be served
_ALLOWED = {g['desktop'] for g in GAMES} | {g['mobile'] for g in GAMES}

# ── Letter recognition (Claude Haiku) ────────────────────────────────────────
_word_img_cache = {}  # word → image URL


def _ddg_images(query, n=1):
    """Fetch up to n DDG image result URLs for query (safe-search on via p=1)."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; arcade/1.0)'}
        vqd_url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}&ia=images"
        req = urllib.request.Request(vqd_url, headers=headers)
        html = urllib.request.urlopen(req, timeout=6).read().decode('utf-8', errors='ignore')
        m = re.search(r'vqd=([^&"\'>\s]+)', html)
        if not m:
            return []
        vqd = m.group(1)
        api_url = (
            "https://duckduckgo.com/i.js?l=us-en&o=json"
            f"&q={urllib.parse.quote(query)}&vqd={vqd}&f=,,,,,&p=1"
        )
        req2 = urllib.request.Request(api_url, headers=headers)
        data = json.loads(urllib.request.urlopen(req2, timeout=6).read())
        return [r['image'] for r in data['results'][:n] if r.get('image')]
    except Exception:
        return []


def _ddg_image(query):
    """Fetch first DDG image result for query. Returns URL string or ''."""
    if query in _word_img_cache:
        return _word_img_cache[query]
    urls = _ddg_images(query, n=1)
    url = urls[0] if urls else ''
    if url:
        _word_img_cache[query] = url
    return url


def _cache_image(url):
    """Download and cache an image locally. Returns /img-cache/ path or original URL on failure."""
    if not url or url.startswith('/img-cache/'):
        return url
    h = hashlib.md5(url.encode()).hexdigest()
    ext = '.jpg'
    clean = url.split('?')[0].lower()
    for e in ('.png', '.gif', '.webp', '.jpeg'):
        if clean.endswith(e):
            ext = '.jpg' if e == '.jpeg' else e
            break
    filename = h + ext
    local_path = os.path.join(IMG_CACHE_DIR, filename)
    if not os.path.exists(local_path):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; arcade/1.0)'}
            req = urllib.request.Request(url, headers=headers)
            data = urllib.request.urlopen(req, timeout=8).read()
            if len(data) > 200:
                with open(local_path, 'wb') as f:
                    f.write(data)
        except Exception:
            return url
    return f'/img-cache/{filename}'


# ── Vocab SQLite DB ───────────────────────────────────────────────────────────

def _vocab_conn():
    return sqlite3.connect(VOCAB_DB, check_same_thread=False)


def _vocab_init():
    con = _vocab_conn()
    cur = con.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS vocab_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lang TEXT NOT NULL,
            level INTEGER NOT NULL,
            word TEXT NOT NULL,
            search TEXT NOT NULL,
            easy_json TEXT NOT NULL,
            hard_json TEXT NOT NULL,
            source TEXT DEFAULT 'builtin',
            UNIQUE(lang, word)
        );
        CREATE TABLE IF NOT EXISTS vocab_images (
            search TEXT NOT NULL,
            url TEXT NOT NULL,
            added_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (search, url)
        );
        CREATE TABLE IF NOT EXISTS vocab_custom_sets (
            id TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            words_json TEXT NOT NULL
        );
    """)

    def js(lst):
        return json.dumps(lst)

    seed = [
        # lang, level, word, search, easy_json, hard_json
        # English level 1
        ('en', 1, 'excavator',  'excavator machine',
         js([{'w':'bee','s':'bee insect'},{'w':'rainbow','s':'rainbow sky'}]),
         js([{'w':'bulldozer','s':'bulldozer machine'},{'w':'dump truck','s':'dump truck vehicle'}])),
        ('en', 1, 'elephant',   'elephant animal',
         js([{'w':'pencil','s':'pencil school'},{'w':'lamp','s':'lamp light'}]),
         js([{'w':'rhinoceros','s':'rhinoceros animal'},{'w':'hippopotamus','s':'hippopotamus animal'}])),
        ('en', 1, 'sunflower',  'sunflower plant',
         js([{'w':'shoe','s':'shoe footwear'},{'w':'clock','s':'clock time'}]),
         js([{'w':'daisy','s':'daisy flower'},{'w':'tulip','s':'tulip flower'}])),
        ('en', 1, 'lighthouse', 'lighthouse coast',
         js([{'w':'butterfly','s':'butterfly insect'},{'w':'fork','s':'fork utensil'}]),
         js([{'w':'windmill','s':'windmill building'},{'w':'water tower','s':'water tower structure'}])),
        ('en', 1, 'pineapple',  'pineapple fruit',
         js([{'w':'hammer','s':'hammer tool'},{'w':'sock','s':'sock clothing'}]),
         js([{'w':'mango','s':'mango fruit'},{'w':'papaya','s':'papaya fruit'}])),
        ('en', 1, 'strawberry', 'strawberry fruit',
         js([{'w':'airplane','s':'airplane aircraft'},{'w':'wrench','s':'wrench tool'}]),
         js([{'w':'raspberry','s':'raspberry fruit'},{'w':'blueberry','s':'blueberry fruit'}])),
        ('en', 1, 'cactus',     'cactus desert',
         js([{'w':'fish','s':'fish animal'},{'w':'bed','s':'bed furniture'}]),
         js([{'w':'aloe vera','s':'aloe vera plant'},{'w':'yucca','s':'yucca plant'}])),
        ('en', 1, 'volcano',    'volcano erupting',
         js([{'w':'cupcake','s':'cupcake dessert'},{'w':'mitten','s':'mitten clothing'}]),
         js([{'w':'mountain','s':'mountain landscape'},{'w':'geyser','s':'geyser nature'}])),
        ('en', 1, 'accordion',  'accordion instrument',
         js([{'w':'apple','s':'apple fruit'},{'w':'ladder','s':'ladder tool'}]),
         js([{'w':'harmonica','s':'harmonica instrument'},{'w':'concertina','s':'concertina instrument'}])),
        ('en', 1, 'flamingo',   'flamingo bird',
         js([{'w':'pizza','s':'pizza food'},{'w':'umbrella','s':'umbrella rain'}]),
         js([{'w':'pelican','s':'pelican bird'},{'w':'heron','s':'heron bird'}])),
        # English level 2
        ('en', 2, 'trebuchet',  'trebuchet siege weapon',
         js([{'w':'fish','s':'fish animal'},{'w':'cupcake','s':'cupcake dessert'}]),
         js([{'w':'catapult','s':'catapult siege weapon'},{'w':'ballista','s':'ballista siege weapon'}])),
        ('en', 2, 'platypus',   'platypus animal',
         js([{'w':'car','s':'car vehicle'},{'w':'house','s':'house building'}]),
         js([{'w':'echidna','s':'echidna animal'},{'w':'beaver','s':'beaver animal'}])),
        ('en', 2, 'mangrove',   'mangrove forest',
         js([{'w':'bicycle','s':'bicycle vehicle'},{'w':'hat','s':'hat clothing'}]),
         js([{'w':'cypress tree','s':'cypress tree forest'},{'w':'banyan tree','s':'banyan tree forest'}])),
        ('en', 2, 'geode',      'geode crystal',
         js([{'w':'sock','s':'sock clothing'},{'w':'spoon','s':'spoon utensil'}]),
         js([{'w':'amethyst','s':'amethyst crystal'},{'w':'quartz','s':'quartz crystal'}])),
        ('en', 2, 'periscope',  'periscope submarine',
         js([{'w':'flower','s':'flower plant'},{'w':'glove','s':'glove clothing'}]),
         js([{'w':'telescope','s':'telescope instrument'},{'w':'kaleidoscope','s':'kaleidoscope toy'}])),
        ('en', 2, 'trowel',     'trowel garden tool',
         js([{'w':'cloud','s':'cloud sky'},{'w':'shoe','s':'shoe footwear'}]),
         js([{'w':'spatula','s':'spatula kitchen tool'},{'w':'palette knife','s':'palette knife art'}])),
        ('en', 2, 'kayak',      'kayak paddling',
         js([{'w':'pencil','s':'pencil school'},{'w':'mushroom','s':'mushroom plant'}]),
         js([{'w':'canoe','s':'canoe boat'},{'w':'rowboat','s':'rowboat boat'}])),
        ('en', 2, 'abacus',     'abacus counting beads',
         js([{'w':'dog','s':'dog animal'},{'w':'balloon','s':'balloon toy'}]),
         js([{'w':'calculator','s':'calculator device'},{'w':'slide rule','s':'slide rule calculator'}])),
        ('en', 2, 'stalactite', 'stalactite cave',
         js([{'w':'apple','s':'apple fruit'},{'w':'lamp','s':'lamp light'}]),
         js([{'w':'stalagmite','s':'stalagmite cave'},{'w':'icicle','s':'icicle ice'}])),
        ('en', 2, 'catamaran',  'catamaran sailboat',
         js([{'w':'chair','s':'chair furniture'},{'w':'tomato','s':'tomato vegetable'}]),
         js([{'w':'trimaran','s':'trimaran sailboat'},{'w':'sailboat','s':'sailboat ocean'}])),
        # Spanish level 1
        ('es', 1, 'excavadora', 'excavator machine',
         js([{'w':'abeja','s':'bee insect'},{'w':'arcoíris','s':'rainbow sky'}]),
         js([{'w':'bulldozer','s':'bulldozer machine'},{'w':'camión volquete','s':'dump truck vehicle'}])),
        ('es', 1, 'elefante',   'elephant animal',
         js([{'w':'lápiz','s':'pencil school'},{'w':'lámpara','s':'lamp light'}]),
         js([{'w':'rinoceronte','s':'rhinoceros animal'},{'w':'hipopótamo','s':'hippopotamus animal'}])),
        ('es', 1, 'girasol',    'sunflower plant',
         js([{'w':'zapato','s':'shoe footwear'},{'w':'reloj','s':'clock time'}]),
         js([{'w':'margarita','s':'daisy flower'},{'w':'tulipán','s':'tulip flower'}])),
        ('es', 1, 'faro',       'lighthouse coast',
         js([{'w':'mariposa','s':'butterfly insect'},{'w':'tenedor','s':'fork utensil'}]),
         js([{'w':'molino de viento','s':'windmill building'},{'w':'torre de agua','s':'water tower structure'}])),
        ('es', 1, 'piña',       'pineapple fruit',
         js([{'w':'martillo','s':'hammer tool'},{'w':'calcetín','s':'sock clothing'}]),
         js([{'w':'mango','s':'mango fruit'},{'w':'papaya','s':'papaya fruit'}])),
        ('es', 1, 'fresa',      'strawberry fruit',
         js([{'w':'avión','s':'airplane aircraft'},{'w':'llave inglesa','s':'wrench tool'}]),
         js([{'w':'frambuesa','s':'raspberry fruit'},{'w':'arándano','s':'blueberry fruit'}])),
        ('es', 1, 'cactus',     'cactus desert',
         js([{'w':'pez','s':'fish animal'},{'w':'cama','s':'bed furniture'}]),
         js([{'w':'aloe vera','s':'aloe vera plant'},{'w':'yuca','s':'yucca plant'}])),
        ('es', 1, 'volcán',     'volcano erupting',
         js([{'w':'pastelito','s':'cupcake dessert'},{'w':'manopla','s':'mitten clothing'}]),
         js([{'w':'montaña','s':'mountain landscape'},{'w':'géiser','s':'geyser nature'}])),
        ('es', 1, 'acordeón',   'accordion instrument',
         js([{'w':'manzana','s':'apple fruit'},{'w':'escalera','s':'ladder tool'}]),
         js([{'w':'armónica','s':'harmonica instrument'},{'w':'concertina','s':'concertina instrument'}])),
        ('es', 1, 'flamenco',   'flamingo bird',
         js([{'w':'pizza','s':'pizza food'},{'w':'paraguas','s':'umbrella rain'}]),
         js([{'w':'pelícano','s':'pelican bird'},{'w':'garza','s':'heron bird'}])),
        # Spanish level 2
        ('es', 2, 'trabuco',         'trebuchet siege weapon',
         js([{'w':'pez','s':'fish animal'},{'w':'pastelito','s':'cupcake dessert'}]),
         js([{'w':'catapulta','s':'catapult siege weapon'},{'w':'ballesta','s':'ballista siege weapon'}])),
        ('es', 2, 'ornitorrinco',    'platypus animal',
         js([{'w':'coche','s':'car vehicle'},{'w':'casa','s':'house building'}]),
         js([{'w':'equidna','s':'echidna animal'},{'w':'castor','s':'beaver animal'}])),
        ('es', 2, 'manglar',         'mangrove forest',
         js([{'w':'bicicleta','s':'bicycle vehicle'},{'w':'sombrero','s':'hat clothing'}]),
         js([{'w':'ciprés','s':'cypress tree forest'},{'w':'baniano','s':'banyan tree forest'}])),
        ('es', 2, 'geoda',           'geode crystal',
         js([{'w':'calcetín','s':'sock clothing'},{'w':'cuchara','s':'spoon utensil'}]),
         js([{'w':'amatista','s':'amethyst crystal'},{'w':'cuarzo','s':'quartz crystal'}])),
        ('es', 2, 'periscopio',      'periscope submarine',
         js([{'w':'flor','s':'flower plant'},{'w':'guante','s':'glove clothing'}]),
         js([{'w':'telescopio','s':'telescope instrument'},{'w':'calidoscopio','s':'kaleidoscope toy'}])),
        ('es', 2, 'paleta de albañil', 'trowel masonry tool',
         js([{'w':'nube','s':'cloud sky'},{'w':'zapato','s':'shoe footwear'}]),
         js([{'w':'espátula','s':'spatula kitchen tool'},{'w':'paleta de pintor','s':'palette knife art'}])),
        ('es', 2, 'kayak',           'kayak paddling',
         js([{'w':'lápiz','s':'pencil school'},{'w':'seta','s':'mushroom plant'}]),
         js([{'w':'canoa','s':'canoe boat'},{'w':'bote de remos','s':'rowboat boat'}])),
        ('es', 2, 'ábaco',           'abacus counting beads',
         js([{'w':'perro','s':'dog animal'},{'w':'globo','s':'balloon toy'}]),
         js([{'w':'calculadora','s':'calculator device'},{'w':'regla de cálculo','s':'slide rule calculator'}])),
        ('es', 2, 'estalactita',     'stalactite cave',
         js([{'w':'manzana','s':'apple fruit'},{'w':'lámpara','s':'lamp light'}]),
         js([{'w':'estalagmita','s':'stalagmite cave'},{'w':'carámbano','s':'icicle ice'}])),
        ('es', 2, 'catamarán',       'catamaran sailboat',
         js([{'w':'silla','s':'chair furniture'},{'w':'tomate','s':'tomato vegetable'}]),
         js([{'w':'trimarán','s':'trimaran sailboat'},{'w':'velero','s':'sailboat ocean'}])),
    ]

    cur.execute("""
        CREATE TABLE IF NOT EXISTS vocab_base (
            lang TEXT NOT NULL,
            idx INTEGER NOT NULL,
            word TEXT NOT NULL,
            search TEXT NOT NULL,
            images_json TEXT NOT NULL DEFAULT '[]',
            PRIMARY KEY (lang, idx)
        )
    """)

    # INSERT OR IGNORE so re-running doesn't duplicate or overwrite
    cur.executemany(
        "INSERT OR IGNORE INTO vocab_words (lang,level,word,search,easy_json,hard_json) VALUES (?,?,?,?,?,?)",
        seed
    )
    con.commit()
    con.close()


# 300 image-definable words per language — seeded once, editable in builder
VOCAB_BASE_EN = [
    # Mammals
    ("elephant","elephant animal"),("giraffe","giraffe animal"),("zebra","zebra animal"),
    ("lion","lion animal"),("tiger","tiger animal"),("gorilla","gorilla primate"),
    ("chimpanzee","chimpanzee monkey"),("kangaroo","kangaroo animal"),("koala","koala animal"),
    ("panda","giant panda"),("hippo","hippopotamus animal"),("rhinoceros","rhinoceros animal"),
    ("camel","camel desert animal"),("llama","llama animal"),("bison","bison animal"),
    ("moose","moose animal"),("platypus","platypus animal"),("armadillo","armadillo animal"),
    ("hedgehog","hedgehog animal"),("sloth","sloth hanging animal"),("meerkat","meerkat animal"),
    ("capybara","capybara animal"),("narwhal","narwhal whale"),("manatee","manatee sea cow"),
    ("pangolin","pangolin animal"),("walrus","walrus animal"),("otter","sea otter animal"),
    ("beaver","beaver animal"),("wolverine","wolverine animal"),("tapir","tapir animal"),
    # Birds
    ("penguin","penguin bird"),("flamingo","flamingo pink bird"),("peacock","peacock feathers bird"),
    ("toucan","toucan colorful bird"),("pelican","pelican bird"),("eagle","bald eagle bird"),
    ("owl","owl bird"),("parrot","parrot colorful bird"),("hummingbird","hummingbird flower"),
    ("ostrich","ostrich bird"),("puffin","puffin seabird"),("kingfisher","kingfisher bird"),
    ("woodpecker","woodpecker bird tree"),("hornbill","hornbill bird beak"),("macaw","macaw parrot"),
    # Sea creatures
    ("dolphin","dolphin ocean"),("whale","whale ocean"),("shark","shark ocean"),
    ("octopus","octopus sea creature"),("jellyfish","jellyfish ocean"),("starfish","starfish ocean"),
    ("lobster","lobster seafood"),("crab","crab seafood"),("seahorse","seahorse ocean"),
    ("seal","seal animal coast"),("squid","squid sea creature"),("sea turtle","sea turtle ocean"),
    ("stingray","stingray ocean"),("clam","clam shell"),("anglerfish","anglerfish deep sea"),
    # Reptiles & insects
    ("crocodile","crocodile reptile"),("iguana","iguana lizard"),("chameleon","chameleon lizard"),
    ("scorpion","scorpion arachnid"),("butterfly","butterfly insect"),("dragonfly","dragonfly insect"),
    ("praying mantis","praying mantis insect"),("caterpillar","caterpillar insect"),
    ("firefly","firefly glowing insect"),("tarantula","tarantula spider"),
    # Vehicles
    ("helicopter","helicopter aircraft"),("submarine","submarine underwater"),
    ("bulldozer","bulldozer construction"),("excavator","excavator machine"),
    ("tractor","tractor farm vehicle"),("ambulance","ambulance emergency vehicle"),
    ("rocket","rocket spacecraft"),("sailboat","sailboat ocean"),("gondola","gondola venice boat"),
    ("kayak","kayak paddling"),("blimp","blimp airship"),("forklift","forklift warehouse"),
    ("hovercraft","hovercraft vehicle"),("hot air balloon","hot air balloon sky"),
    ("glider","glider aircraft"),("snowplow","snowplow truck"),("cable car","cable car trolley"),
    ("canoe","canoe paddling"),("ferry","ferry boat"),("rickshaw","rickshaw vehicle"),
    # Food
    ("pineapple","pineapple fruit"),("watermelon","watermelon fruit"),("strawberry","strawberry fruit"),
    ("coconut","coconut tropical"),("avocado","avocado fruit"),("broccoli","broccoli vegetable"),
    ("cauliflower","cauliflower vegetable"),("eggplant","eggplant vegetable"),
    ("artichoke","artichoke vegetable"),("asparagus","asparagus vegetable"),
    ("baguette","baguette french bread"),("pretzel","pretzel snack"),("donut","donut pastry"),
    ("croissant","croissant pastry"),("waffle","waffle breakfast"),("sushi","sushi japanese food"),
    ("taco","taco mexican food"),("dumpling","dumpling chinese food"),
    ("pomegranate","pomegranate fruit"),("dragon fruit","dragon fruit tropical"),
    # Objects & tools
    ("hourglass","hourglass sand timer"),("compass","compass navigation tool"),
    ("telescope","telescope astronomy"),("microscope","microscope science lab"),
    ("lantern","lantern light"),("chandelier","chandelier ceiling light"),
    ("typewriter","typewriter machine"),("gramophone","gramophone record player"),
    ("trophy","trophy award gold"),("globe","globe world sphere"),
    ("abacus","abacus counting beads"),("periscope","periscope instrument"),
    ("kaleidoscope","kaleidoscope toy"),("metronome","metronome music"),("vase","flower vase"),
    ("sundial","sundial time"),("thermometer","thermometer temperature"),
    ("magnifying glass","magnifying glass"),("anvil","anvil blacksmith"),
    ("mortar and pestle","mortar and pestle kitchen"),
    ("pulley","pulley rope machine"),("bellows","bellows fire tool"),("easel","easel painting art"),
    ("chisel","chisel woodcarving tool"),("mallet","wooden mallet"),("wrench","wrench tool"),
    ("trowel","trowel masonry tool"),("crowbar","crowbar tool"),("pliers","pliers tool"),
    ("sextant","sextant navigation"),
    # Clothing
    ("tiara","tiara crown headwear"),("turban","turban headwear"),("sombrero","sombrero hat"),
    ("beret","beret hat"),("kimono","kimono japanese clothing"),("sari","sari indian clothing"),
    ("kilt","kilt scottish clothing"),("overalls","overalls farming clothing"),
    ("top hat","top hat magician"),("cloak","cloak cape clothing"),
    # Buildings
    ("igloo","igloo ice house"),("pyramid","pyramid egypt"),("lighthouse","lighthouse coast"),
    ("windmill","windmill building"),("castle","castle medieval"),("pagoda","pagoda asian temple"),
    ("mosque","mosque dome building"),("cathedral","cathedral gothic church"),
    ("greenhouse","greenhouse glass garden"),("treehouse","treehouse wood platform"),
    ("barn","barn red farm building"),("silo","grain silo farm"),("aqueduct","roman aqueduct"),
    ("gazebo","gazebo garden"),("teepee","teepee native american"),("yurt","yurt nomad home"),
    ("log cabin","log cabin forest"),("colosseum","colosseum rome"),("sphinx","great sphinx egypt"),
    ("drawbridge","drawbridge castle"),
    # Nature
    ("volcano","volcano erupting lava"),("glacier","glacier ice"),("canyon","canyon red rock"),
    ("geyser","geyser steam water"),("stalactite","stalactite cave"),("iceberg","iceberg ocean"),
    ("coral reef","coral reef underwater"),("mangrove","mangrove forest roots"),
    ("fjord","fjord norway"),("oasis","oasis desert palm trees"),("lagoon","lagoon tropical water"),
    ("mesa","mesa desert plateau"),("dune","sand dune desert"),("waterfall","waterfall nature"),
    ("cave","cave underground"),("cliff","cliff coastal rock"),("tide pool","tide pool ocean"),
    ("hot spring","hot spring geothermal pool"),
    ("aurora","aurora borealis northern lights"),("delta","river delta aerial view"),
    # Plants
    ("cactus","cactus desert"),("orchid","orchid flower"),("lotus","lotus flower water"),
    ("bonsai","bonsai tree"),("bamboo","bamboo plant"),
    ("venus flytrap","venus flytrap carnivorous plant"),("sunflower","sunflower yellow"),
    ("lavender","lavender purple field"),("tulip","tulip flower"),
    ("magnolia","magnolia flower tree"),("toadstool","red toadstool mushroom"),
    ("fern","fern plant green"),("seaweed","seaweed ocean plant"),
    ("dandelion","dandelion flower"),("poppy","poppy red flower"),
    ("mistletoe","mistletoe plant"),("pitcher plant","pitcher plant carnivorous"),
    ("pine cone","pine cone nature"),("acorn","acorn oak nut"),("clover","clover plant green"),
    # Musical instruments
    ("accordion","accordion instrument"),("banjo","banjo instrument"),("cello","cello instrument"),
    ("clarinet","clarinet instrument"),("didgeridoo","didgeridoo aboriginal instrument"),
    ("French horn","french horn instrument"),("gong","gong percussion"),
    ("harmonica","harmonica instrument"),("harp","harp instrument"),("lute","lute instrument"),
    ("maracas","maracas percussion"),("oboe","oboe instrument"),("sitar","sitar indian instrument"),
    ("tambourine","tambourine percussion"),("trombone","trombone instrument"),
    ("tuba","tuba instrument"),("ukulele","ukulele instrument"),("xylophone","xylophone instrument"),
    ("bagpipes","bagpipes scottish instrument"),("zither","zither instrument"),
    # Sports
    ("archery","archery bow arrow"),("boomerang","boomerang australia"),
    ("curling","curling sport ice"),("fencing","fencing sword sport"),
    ("javelin","javelin throw sport"),("lacrosse","lacrosse stick sport"),
    ("skateboard","skateboard sport"),("surfboard","surfboard ocean wave"),
    ("trampoline","trampoline jumping"),("discus","discus throw sport"),
    ("luge","luge winter sport sled"),("bobsled","bobsled winter sport"),
    ("polo","polo horse sport"),("shuffleboard","shuffleboard game"),("darts","darts board game"),
    # Space & science
    ("asteroid","asteroid space rock"),("comet","comet space tail"),
    ("nebula","nebula space colorful"),("satellite","satellite orbit space"),
    ("space station","international space station"),("black hole","black hole illustration"),
    ("meteor","meteor shooting star"),("solar eclipse","solar eclipse"),
    ("constellation","constellation star map"),("supernova","supernova explosion space"),
    ("galaxy","spiral galaxy space"),("crater","meteor impact crater"),
    ("observatory","telescope observatory dome"),("solar panel","solar panel energy"),
    ("wind turbine","wind turbine renewable energy"),
    # Toys, games & misc
    ("pinwheel","pinwheel toy wind"),("kite","kite flying sky"),("yo-yo","yo-yo toy"),
    ("marionette","marionette puppet"),("chess","chess board pieces"),
    ("dominoes","dominoes game tiles"),("spinning top","spinning top toy"),
    ("origami","origami paper crane"),("dreamcatcher","dreamcatcher wall hanging"),
    ("mosaic","mosaic tile art"),("labyrinth","labyrinth maze"),
    ("pinata","pinata colorful party"),("puppet","hand puppet toy"),
    ("boomerang","boomerang australia"),("lego","lego colorful bricks"),
]

VOCAB_BASE_ES = [
    # Mammals
    ("elefante","elephant animal"),("jirafa","giraffe animal"),("cebra","zebra animal"),
    ("león","lion animal"),("tigre","tiger animal"),("gorila","gorilla primate"),
    ("chimpancé","chimpanzee monkey"),("canguro","kangaroo animal"),("koala","koala animal"),
    ("panda","giant panda"),("hipopótamo","hippopotamus animal"),("rinoceronte","rhinoceros animal"),
    ("camello","camel desert animal"),("llama","llama animal"),("bisonte","bison animal"),
    ("alce","moose animal"),("ornitorrinco","platypus animal"),("armadillo","armadillo animal"),
    ("erizo","hedgehog animal"),("perezoso","sloth hanging animal"),("suricata","meerkat animal"),
    ("capibara","capybara animal"),("narval","narwhal whale"),("manatí","manatee sea cow"),
    ("pangolín","pangolin animal"),("morsa","walrus animal"),("nutria","sea otter animal"),
    ("castor","beaver animal"),("glotón","wolverine animal"),("tapir","tapir animal"),
    # Birds
    ("pingüino","penguin bird"),("flamenco","flamingo pink bird"),("pavo real","peacock feathers bird"),
    ("tucán","toucan colorful bird"),("pelícano","pelican bird"),("águila","bald eagle bird"),
    ("búho","owl bird"),("loro","parrot colorful bird"),("colibrí","hummingbird flower"),
    ("avestruz","ostrich bird"),("frailecillo","puffin seabird"),("martín pescador","kingfisher bird"),
    ("pájaro carpintero","woodpecker bird tree"),("cálao","hornbill bird beak"),("guacamayo","macaw parrot"),
    # Sea creatures
    ("delfín","dolphin ocean"),("ballena","whale ocean"),("tiburón","shark ocean"),
    ("pulpo","octopus sea creature"),("medusa","jellyfish ocean"),("estrella de mar","starfish ocean"),
    ("langosta","lobster seafood"),("cangrejo","crab seafood"),("caballito de mar","seahorse ocean"),
    ("foca","seal animal coast"),("calamar","squid sea creature"),("tortuga marina","sea turtle ocean"),
    ("mantarraya","stingray ocean"),("almeja","clam shell"),("pez linterna","anglerfish deep sea"),
    # Reptiles & insects
    ("cocodrilo","crocodile reptile"),("iguana","iguana lizard"),("camaleón","chameleon lizard"),
    ("escorpión","scorpion arachnid"),("mariposa","butterfly insect"),("libélula","dragonfly insect"),
    ("mantis religiosa","praying mantis insect"),("oruga","caterpillar insect"),
    ("luciérnaga","firefly glowing insect"),("tarántula","tarantula spider"),
    # Vehicles
    ("helicóptero","helicopter aircraft"),("submarino","submarine underwater"),
    ("bulldozer","bulldozer construction"),("excavadora","excavator machine"),
    ("tractor","tractor farm vehicle"),("ambulancia","ambulance emergency vehicle"),
    ("cohete","rocket spacecraft"),("velero","sailboat ocean"),("góndola","gondola venice boat"),
    ("kayak","kayak paddling"),("dirigible","blimp airship"),("montacargas","forklift warehouse"),
    ("aerodeslizador","hovercraft vehicle"),("globo aerostático","hot air balloon sky"),
    ("planeador","glider aircraft"),("quitanieves","snowplow truck"),("teleférico","cable car trolley"),
    ("canoa","canoe paddling"),("ferry","ferry boat"),("rickshaw","rickshaw vehicle"),
    # Food
    ("piña","pineapple fruit"),("sandía","watermelon fruit"),("fresa","strawberry fruit"),
    ("coco","coconut tropical"),("aguacate","avocado fruit"),("brócoli","broccoli vegetable"),
    ("coliflor","cauliflower vegetable"),("berenjena","eggplant vegetable"),
    ("alcachofa","artichoke vegetable"),("espárragos","asparagus vegetable"),
    ("baguette","baguette french bread"),("pretzel","pretzel snack"),("dona","donut pastry"),
    ("croissant","croissant pastry"),("gofre","waffle breakfast"),("sushi","sushi japanese food"),
    ("taco","taco mexican food"),("dumpling","dumpling chinese food"),
    ("granada","pomegranate fruit"),("pitahaya","dragon fruit tropical"),
    # Objects & tools
    ("reloj de arena","hourglass sand timer"),("brújula","compass navigation tool"),
    ("telescopio","telescope astronomy"),("microscopio","microscope science lab"),
    ("linterna","lantern light"),("araña de luces","chandelier ceiling light"),
    ("máquina de escribir","typewriter machine"),("gramófono","gramophone record player"),
    ("trofeo","trophy award gold"),("globo terráqueo","globe world sphere"),
    ("ábaco","abacus counting beads"),("periscopio","periscope instrument"),
    ("caleidoscopio","kaleidoscope toy"),("metrónomo","metronome music"),("florero","flower vase"),
    ("reloj solar","sundial time"),("termómetro","thermometer temperature"),
    ("lupa","magnifying glass"),("yunque","anvil blacksmith"),("mortero","mortar and pestle kitchen"),
    ("polea","pulley rope machine"),("fuelle","bellows fire tool"),("caballete","easel painting art"),
    ("cincel","chisel woodcarving tool"),("mazo","wooden mallet"),("llave inglesa","wrench tool"),
    ("paleta de albañil","trowel masonry tool"),("palanca","crowbar tool"),("alicates","pliers tool"),
    ("sextante","sextant navigation"),
    # Clothing
    ("tiara","tiara crown headwear"),("turbante","turban headwear"),("sombrero","sombrero hat"),
    ("boina","beret hat"),("kimono","kimono japanese clothing"),("sari","sari indian clothing"),
    ("kilt","kilt scottish clothing"),("overol","overalls farming clothing"),
    ("chistera","top hat magician"),("capa","cloak cape clothing"),
    # Buildings
    ("iglú","igloo ice house"),("pirámide","pyramid egypt"),("faro","lighthouse coast"),
    ("molino de viento","windmill building"),("castillo","castle medieval"),
    ("pagoda","pagoda asian temple"),("mezquita","mosque dome building"),
    ("catedral","cathedral gothic church"),("invernadero","greenhouse glass garden"),
    ("casa en el árbol","treehouse wood platform"),("granero","barn red farm building"),
    ("silo","grain silo farm"),("acueducto","roman aqueduct"),("cenador","gazebo garden"),
    ("tipi","teepee native american"),("yurta","yurt nomad home"),
    ("cabaña de troncos","log cabin forest"),("coliseo","colosseum rome"),
    ("esfinge","great sphinx egypt"),("puente levadizo","drawbridge castle"),
    # Nature
    ("volcán","volcano erupting lava"),("glaciar","glacier ice"),("cañón","canyon red rock"),
    ("géiser","geyser steam water"),("estalactita","stalactite cave"),("iceberg","iceberg ocean"),
    ("arrecife de coral","coral reef underwater"),("manglar","mangrove forest roots"),
    ("fiordo","fjord norway"),("oasis","oasis desert palm trees"),("laguna","lagoon tropical water"),
    ("meseta","mesa desert plateau"),("duna","sand dune desert"),("cascada","waterfall nature"),
    ("cueva","cave underground"),("acantilado","cliff coastal rock"),("poza de marea","tide pool ocean"),
    ("manantial caliente","hot spring geothermal pool"),
    ("aurora boreal","aurora borealis northern lights"),("delta","river delta aerial view"),
    # Plants
    ("cactus","cactus desert"),("orquídea","orchid flower"),("loto","lotus flower water"),
    ("bonsái","bonsai tree"),("bambú","bamboo plant"),
    ("venus atrapamoscas","venus flytrap carnivorous plant"),("girasol","sunflower yellow"),
    ("lavanda","lavender purple field"),("tulipán","tulip flower"),
    ("magnolia","magnolia flower tree"),("seta venenosa","red toadstool mushroom"),
    ("helecho","fern plant green"),("alga marina","seaweed ocean plant"),
    ("diente de león","dandelion flower"),("amapola","poppy red flower"),
    ("muérdago","mistletoe plant"),("planta jarro","pitcher plant carnivorous"),
    ("piña de pino","pine cone nature"),("bellota","acorn oak nut"),("trébol","clover plant green"),
    # Musical instruments
    ("acordeón","accordion instrument"),("banjo","banjo instrument"),("violonchelo","cello instrument"),
    ("clarinete","clarinet instrument"),("didyeridú","didgeridoo aboriginal instrument"),
    ("trompa","french horn instrument"),("gong","gong percussion"),
    ("armónica","harmonica instrument"),("arpa","harp instrument"),("laúd","lute instrument"),
    ("maracas","maracas percussion"),("oboe","oboe instrument"),("sitar","sitar indian instrument"),
    ("pandereta","tambourine percussion"),("trombón","trombone instrument"),
    ("tuba","tuba instrument"),("ukelele","ukulele instrument"),("xilófono","xylophone instrument"),
    ("gaita","bagpipes scottish instrument"),("cítara","zither instrument"),
    # Sports
    ("tiro con arco","archery bow arrow"),("bumerán","boomerang australia"),
    ("curling","curling sport ice"),("esgrima","fencing sword sport"),
    ("jabalina","javelin throw sport"),("lacrosse","lacrosse stick sport"),
    ("monopatín","skateboard sport"),("tabla de surf","surfboard ocean wave"),
    ("trampolín","trampoline jumping"),("disco","discus throw sport"),
    ("luge","luge winter sport sled"),("bobsled","bobsled winter sport"),
    ("polo","polo horse sport"),("shuffleboard","shuffleboard game"),("dardos","darts board game"),
    # Space & science
    ("asteroide","asteroid space rock"),("cometa","comet space tail"),
    ("nebulosa","nebula space colorful"),("satélite","satellite orbit space"),
    ("estación espacial","international space station"),("agujero negro","black hole illustration"),
    ("meteoro","meteor shooting star"),("eclipse solar","solar eclipse"),
    ("constelación","constellation star map"),("supernova","supernova explosion space"),
    ("galaxia","spiral galaxy space"),("cráter","meteor impact crater"),
    ("observatorio","telescope observatory dome"),("panel solar","solar panel energy"),
    ("turbina eólica","wind turbine renewable energy"),
    # Toys, games & misc
    ("molinillo","pinwheel toy wind"),("cometa de papel","kite flying sky"),("yoyó","yo-yo toy"),
    ("marioneta","marionette puppet"),("ajedrez","chess board pieces"),
    ("dominó","dominoes game tiles"),("trompo","spinning top toy"),
    ("origami","origami paper crane"),("atrapasueños","dreamcatcher wall hanging"),
    ("mosaico","mosaic tile art"),("laberinto","labyrinth maze"),
    ("piñata","pinata colorful party"),("títere","hand puppet toy"),
    ("bloques de construcción","lego colorful bricks"),("ruleta","roulette wheel game"),
]


def _seed_vocab_base():
    con = _vocab_conn()
    cur = con.cursor()
    for lang, words in (('en', VOCAB_BASE_EN), ('es', VOCAB_BASE_ES)):
        cur.executemany(
            "INSERT OR IGNORE INTO vocab_base (lang, idx, word, search) VALUES (?,?,?,?)",
            [(lang, i, w, s) for i, (w, s) in enumerate(words)]
        )
    con.commit()
    con.close()


_vocab_init()
_seed_vocab_base()


def _vocab_get_images(search, n=4):
    con = _vocab_conn()
    cur = con.cursor()
    rows = cur.execute(
        "SELECT url FROM vocab_images WHERE search=? LIMIT ?", (search, n)
    ).fetchall()
    urls = [r[0] for r in rows]
    if len(urls) >= n:
        con.close()
        return urls
    fetched = _ddg_images(search, n=6)
    if fetched:
        cur.executemany(
            "INSERT OR IGNORE INTO vocab_images (search,url) VALUES (?,?)",
            [(search, u) for u in fetched]
        )
        con.commit()
        all_rows = cur.execute(
            "SELECT url FROM vocab_images WHERE search=? LIMIT ?", (search, n)
        ).fetchall()
        urls = [r[0] for r in all_rows]
    con.close()
    return urls


def _slugify(text):
    slug = re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')
    return slug or 'set'


def _load_custom_sets():
    try:
        with open(CUSTOM_SETS_FILE) as f:
            return json.load(f).get('sets', [])
    except FileNotFoundError:
        return []


def _save_custom_sets(sets):
    try:
        with open(CUSTOM_SETS_FILE) as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    data['sets'] = sets
    with open(CUSTOM_SETS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def _load_spelling_sets():
    try:
        with open(CUSTOM_SETS_FILE) as f:
            return json.load(f).get('spelling_sets', [])
    except FileNotFoundError:
        return []


def _save_spelling_sets(sets):
    try:
        with open(CUSTOM_SETS_FILE) as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    data['spelling_sets'] = sets
    with open(CUSTOM_SETS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def _load_item_sets():
    try:
        with open(CUSTOM_SETS_FILE) as f:
            return json.load(f).get('item_sets', [])
    except FileNotFoundError:
        return []


def _save_item_sets(sets):
    try:
        with open(CUSTOM_SETS_FILE) as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    data['item_sets'] = sets
    with open(CUSTOM_SETS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def _load_ss_word_sets():
    try:
        with open(CUSTOM_SETS_FILE) as f:
            return json.load(f).get('ss_word_sets', [])
    except FileNotFoundError:
        return []


def _save_ss_word_sets(sets):
    try:
        with open(CUSTOM_SETS_FILE) as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    data['ss_word_sets'] = sets
    with open(CUSTOM_SETS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html', games=GAMES)


@app.route('/games/<path:filename>')
def serve_game(filename):
    if filename not in _ALLOWED:
        abort(404)
    return send_from_directory(BASE_DIR, filename)


@app.route('/audio/<path:filename>')
def serve_audio(filename):
    # Sound Speller pulls phonemes from audio/phonemes/ and digraphs are uppercase (SH, TH, OA…)
    if not re.fullmatch(r'(phonemes/)?[A-Za-z0-9_]+\.mp3', filename):
        abort(404)
    audio_dir = os.path.join(BASE_DIR, 'audio')
    if not os.path.isfile(os.path.join(audio_dir, filename)):
        abort(404)
    return send_from_directory(audio_dir, filename)


@app.route('/images/<path:filename>')
def serve_image(filename):
    if not re.fullmatch(r'[a-z0-9_\-]+\.(png|jpg|jpeg|gif|webp|svg)', filename):
        abort(404)
    img_dir = os.path.join(BASE_DIR, 'images')
    if not os.path.isfile(os.path.join(img_dir, filename)):
        abort(404)
    return send_from_directory(img_dir, filename)


@app.route('/img-cache/<filename>')
def serve_img_cache(filename):
    if not re.fullmatch(r'[a-f0-9]{32}\.(jpg|png|gif|webp)', filename):
        abort(404)
    filepath = os.path.join(IMG_CACHE_DIR, filename)
    if not os.path.isfile(filepath):
        abort(404)
    return send_from_directory(IMG_CACHE_DIR, filename)


@app.route('/img-cache/<game>/<filename>')
def serve_game_img_cache(game, filename):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', game):
        abort(404)
    if not re.fullmatch(r'[a-zA-Z0-9_-]+\.(jpg|png|gif|webp)', filename):
        abort(404)
    game_dir = os.path.join(IMG_CACHE_DIR, game)
    if not os.path.isfile(os.path.join(game_dir, filename)):
        abort(404)
    return send_from_directory(game_dir, filename)


_tts_cache = {}  # (word, lang) → cached mp3 bytes

@app.route('/api/tts')
def tts_word():
    word = request.args.get('word', '').strip()[:40]
    lang = request.args.get('lang', 'en').strip()[:5]
    if lang not in ('en', 'es', 'fr', 'de', 'pt', 'it', 'ja', 'zh'):
        lang = 'en'
    # Allow unicode letters for Spanish words (ñ, á, etc.)
    if not word or not re.match(r'^[\w\s\'\-áéíóúüñÁÉÍÓÚÜÑ]+$', word, re.UNICODE):
        abort(400)
    key = (word.lower(), lang)
    if key not in _tts_cache:
        try:
            from gtts import gTTS
            import io as _io
            buf = _io.BytesIO()
            gTTS(text=word, lang=lang, slow=True).write_to_fp(buf)
            _tts_cache[key] = buf.getvalue()
        except Exception:
            abort(500)
    from flask import Response
    return Response(_tts_cache[key], mimetype='audio/mpeg')


@app.route('/api/settings', methods=['GET'])
def get_settings():
    try:
        with open(SETTINGS_FILE) as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify({})


@app.route('/api/settings', methods=['POST'])
def save_settings():
    data = request.get_json(force=True, silent=True) or {}
    try:
        existing = {}
        try:
            with open(SETTINGS_FILE) as f:
                existing = json.load(f)
        except FileNotFoundError:
            pass
        existing.update(data)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(existing, f)
    except Exception:
        pass
    return '', 204


@app.route('/api/custom-sets', methods=['GET'])
def list_custom_sets():
    return jsonify({'sets': _load_custom_sets()})


@app.route('/api/custom-sets/preview', methods=['POST'])
def preview_custom_set():
    data = request.get_json(force=True, silent=True) or {}
    bins = data.get('bins', [])
    if not (2 <= len(bins) <= 4):
        return jsonify({'error': 'need 2-4 bins'}), 400

    out_bins = []
    for b in bins:
        label = (b.get('label') or '').strip()
        query = (b.get('query') or label).strip()
        if not label or not query:
            return jsonify({'error': 'each bin needs a label'}), 400
        images = _ddg_images(query, n=10)
        out_bins.append({'label': label, 'query': query, 'images': images})
    return jsonify({'bins': out_bins})


@app.route('/api/custom-sets', methods=['POST'])
def create_custom_set():
    data = request.get_json(force=True, silent=True) or {}
    label = (data.get('label') or '').strip()
    bins = data.get('bins', [])
    if not label or not (2 <= len(bins) <= 4):
        return jsonify({'error': 'need a label and 2-4 bins'}), 400

    clean_bins = []
    for b in bins:
        blabel = (b.get('label') or '').strip()
        images = [u for u in b.get('images', []) if isinstance(u, str) and (u.startswith('http') or u.startswith('/img-cache/'))]
        if not blabel or len(images) < 2:
            return jsonify({'error': 'each bin needs a label and at least 2 images'}), 400
        cached = [_cache_image(u) for u in images]
        clean_bins.append({
            'key':    _slugify(blabel),
            'label':  blabel,
            'icon':   (b.get('icon') or '📦')[:8],
            'images': cached,
        })

    sets = _load_custom_sets()
    base_id = _slugify(label)
    existing_ids = {s['id'] for s in sets}
    set_id = base_id
    i = 2
    while set_id in existing_ids:
        set_id = f"{base_id}_{i}"
        i += 1

    new_set = {'id': set_id, 'label': label, 'bins': clean_bins}
    sets.append(new_set)
    _save_custom_sets(sets)
    return jsonify(new_set), 201


@app.route('/api/custom-sets/<set_id>', methods=['DELETE'])
def delete_custom_set(set_id):
    sets = _load_custom_sets()
    sets = [s for s in sets if s['id'] != set_id]
    _save_custom_sets(sets)
    return '', 204


@app.route('/api/spelling-sets', methods=['GET'])
def list_spelling_sets():
    return jsonify({'sets': _load_spelling_sets()})


@app.route('/api/spelling-sets/default', methods=['GET'])
def get_default_spelling_set():
    sets = _load_spelling_sets()
    default = next((s for s in sets if s.get('id') == 'default'), None)
    if not default:
        default = {
            'id': 'default', 'label': 'Default Word Set',
            'words': ['ELEPHANT','GIRAFFE','PENGUIN','BUTTERFLY','PINEAPPLE',
                      'VOLCANO','LIGHTHOUSE','ACCORDION','STRAWBERRY','TELESCOPE'],
            'word_search': {
                'ELEPHANT':'elephant animal','GIRAFFE':'giraffe animal',
                'PENGUIN':'penguin bird','BUTTERFLY':'butterfly insect',
                'PINEAPPLE':'pineapple fruit','VOLCANO':'volcano erupting',
                'LIGHTHOUSE':'lighthouse coast','ACCORDION':'accordion instrument',
                'STRAWBERRY':'strawberry fruit','TELESCOPE':'telescope astronomy',
            }
        }
    return jsonify(default)


@app.route('/api/spelling-sets', methods=['POST'])
def create_spelling_set():
    data = request.get_json(force=True, silent=True) or {}
    label = (data.get('label') or '').strip()
    words = data.get('words', [])
    if not label:
        return jsonify({'error': 'need a label'}), 400
    clean = [w.strip().upper() for w in words if isinstance(w, str) and w.strip()]
    clean = [w for w in clean if re.match(r"^[A-Z][A-Z'\- ]*$", w)]
    if len(clean) < 2:
        return jsonify({'error': 'need at least 2 valid words'}), 400

    # Optional per-word picked image URLs: { "WORD": url_or_list }
    word_images_raw = data.get('word_images') or {}
    if not isinstance(word_images_raw, dict):
        word_images_raw = {}
    word_images = {}
    for k, v in word_images_raw.items():
        if isinstance(v, list):
            urls = [u for u in v if isinstance(u, str) and u]
            if urls:
                word_images[k] = urls
        elif isinstance(v, str) and v:
            word_images[k] = [v]

    # Optional per-word search terms: { "WORD": "search term" }
    word_search_raw = data.get('word_search') or {}
    if not isinstance(word_search_raw, dict):
        word_search_raw = {}
    word_search = {
        k.upper().strip(): str(v).strip()
        for k, v in word_search_raw.items()
        if v and isinstance(v, str) and str(v).strip()
    }

    sets = _load_spelling_sets()
    # For the default set, update in place instead of appending
    set_id_requested = data.get('id', '').strip()
    if set_id_requested == 'default':
        sets = [s for s in sets if s.get('id') != 'default']
        new_set = {'id': 'default', 'label': label, 'words': clean}
        if word_images:
            new_set['word_images'] = word_images
        if word_search:
            new_set['word_search'] = word_search
        sets.insert(0, new_set)
        _save_spelling_sets(sets)
        return jsonify(new_set), 201

    base_id = _slugify(label)
    existing_ids = {s['id'] for s in sets}
    set_id = base_id
    i = 2
    while set_id in existing_ids:
        set_id = f"{base_id}_{i}"
        i += 1
    new_set = {'id': set_id, 'label': label, 'words': clean}
    if word_images:
        new_set['word_images'] = word_images
    if word_search:
        new_set['word_search'] = word_search
    sets.append(new_set)
    _save_spelling_sets(sets)
    return jsonify(new_set), 201


@app.route('/api/spelling-sets/<set_id>', methods=['DELETE'])
def delete_spelling_set(set_id):
    sets = [s for s in _load_spelling_sets() if s['id'] != set_id]
    _save_spelling_sets(sets)
    return '', 204


@app.route('/api/images/search', methods=['POST'])
def images_search():
    data = request.get_json(force=True, silent=True) or {}
    query = (data.get('query') or '').strip()
    if not query or len(query) > 120:
        return jsonify({'error': 'query required'}), 400
    images = _ddg_images(query, n=12)
    return jsonify({'images': images})


@app.route('/api/item-sets', methods=['GET'])
def list_item_sets():
    return jsonify({'sets': _load_item_sets()})


@app.route('/api/item-sets', methods=['POST'])
def create_item_set():
    data = request.get_json(force=True, silent=True) or {}
    label = (data.get('label') or '').strip()
    images = data.get('images', [])
    if not label:
        return jsonify({'error': 'need a label'}), 400
    clean = [u for u in images if isinstance(u, str) and (u.startswith('http') or u.startswith('/img-cache/'))]
    if len(clean) < 2:
        return jsonify({'error': 'need at least 2 images'}), 400
    cached = [_cache_image(u) for u in clean]

    sets = _load_item_sets()
    base_id = _slugify(label)
    existing_ids = {s['id'] for s in sets}
    set_id = base_id
    i = 2
    while set_id in existing_ids:
        set_id = f'{base_id}_{i}'
        i += 1
    new_set = {'id': set_id, 'label': label, 'images': cached}
    sets.append(new_set)
    _save_item_sets(sets)
    return jsonify(new_set), 201


@app.route('/api/item-sets/<set_id>', methods=['DELETE'])
def delete_item_set(set_id):
    sets = [s for s in _load_item_sets() if s['id'] != set_id]
    _save_item_sets(sets)
    return '', 204


@app.route('/api/word-image')
def word_image():
    word = re.sub(r'[^a-zA-Z\s]', '', request.args.get('word', '').strip().lower())[:40]
    if not word:
        return jsonify({'url': None})
    imgs = _ddg_images(word, n=4)
    for url in imgs:
        cached = _cache_image(url)
        if cached and cached.startswith('/img-cache/'):
            return jsonify({'url': cached})
    return jsonify({'url': None})


@app.route('/api/ss-word-sets', methods=['GET'])
def list_ss_word_sets():
    return jsonify({'sets': _load_ss_word_sets()})


@app.route('/api/ss-word-sets', methods=['POST'])
def create_ss_word_set():
    data = request.get_json(force=True, silent=True) or {}
    label = (data.get('label') or '').strip()[:60]
    raw = data.get('words', [])
    words = [w.strip().lower() for w in raw if isinstance(w, str) and w.strip()]
    words = [w for w in words if re.match(r'^[a-z]{2,20}$', w)][:100]
    if not label or len(words) < 1:
        return jsonify({'error': 'label and at least 1 word required'}), 400
    set_id = 'ssw_' + hashlib.md5((label + '|' + ','.join(words)).encode()).hexdigest()[:8]
    sets = _load_ss_word_sets()
    new_set = {'id': set_id, 'label': label, 'words': words}
    sets.append(new_set)
    _save_ss_word_sets(sets)
    return jsonify(new_set), 201


@app.route('/api/ss-word-sets/<set_id>', methods=['DELETE'])
def delete_ss_word_set(set_id):
    sets = [s for s in _load_ss_word_sets() if s['id'] != set_id]
    _save_ss_word_sets(sets)
    return '', 204


@app.route('/api/letter-words')
def letter_words():
    letter = request.args.get('letter', 'A').upper()
    words_file = os.path.join(BASE_DIR, 'letter_words.json')
    try:
        with open(words_file) as f:
            words_map = json.load(f)
    except FileNotFoundError:
        words_map = {}
    words = words_map.get(letter, [letter.lower()])
    word = random.choice(words)
    img_url = _ddg_image(word)
    return jsonify({'word': word, 'image': img_url})


@app.route('/api/recognize-letter', methods=['POST'])
def recognize_letter():
    """Use Claude Haiku vision to identify the handwritten letter."""
    import anthropic
    import numpy as np
    from PIL import Image

    data = request.get_json(force=True)
    if not data or 'image' not in data:
        return jsonify({'error': 'missing image'}), 400

    img_data = data['image']
    _, b64 = img_data.split(',', 1) if ',' in img_data else ('', img_data)

    # Crop to ink bounding box so Haiku gets a clean, well-framed letter
    img_bytes = base64.b64decode(b64)
    img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
    gray = np.array(img.convert('L'))
    dark = gray < 200
    rows, cols = dark.any(axis=1), dark.any(axis=0)
    if rows.any() and cols.any():
        r0, r1 = int(rows.argmax()), int(len(rows) - rows[::-1].argmax())
        c0, c1 = int(cols.argmax()), int(len(cols) - cols[::-1].argmax())
        pad = max(r1 - r0, c1 - c0) // 5
        r0 = max(0, r0 - pad); r1 = min(gray.shape[0], r1 + pad)
        c0 = max(0, c0 - pad); c1 = min(gray.shape[1], c1 + pad)
        img = img.crop((c0, r0, c1, r1))

    img = img.resize((280, 280), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    b64_clean = base64.b64encode(buf.getvalue()).decode()

    target = (data.get('target') or '').strip().upper()
    stroke_count = data.get('stroke_count', '?')

    if not (len(target) == 1 and target.isalpha()):
        return jsonify({'error': 'missing target letter'}), 400

    prompt = (
        f"A young child (pre-K/kindergarten, age 3-6) is practicing writing the "
        f"uppercase letter '{target}'. They used {stroke_count} stroke(s). "
        f"Does this drawing show a reasonable attempt at '{target}'? "
        f"Be encouraging and lenient — wobbly or partial shapes count if the "
        f"general form is recognizable. Reply with exactly one word: YES or NO."
    )

    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=5,
            messages=[{'role': 'user', 'content': [
                {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': b64_clean}},
                {'type': 'text', 'text': prompt},
            ]}],
        )
        accepted = msg.content[0].text.strip().upper().startswith('Y')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'accepted': accepted, 'letter': target})


# ── Vocab Builder routes ──────────────────────────────────────────────────────

def _build_rounds(words, mode):
    rounds = []
    for row in words:
        word, search, easy_json, hard_json = row[2], row[3], row[4], row[5]
        distractors = json.loads(easy_json if mode == 'easy' else hard_json)
        target_imgs = [_cache_image(u) for u in _vocab_get_images(search, n=3) if u]
        choices = [{'word': word, 'display_word': word, 'images': target_imgs, 'correct': True}]
        for d in distractors[:2]:
            d_imgs = [_cache_image(u) for u in _vocab_get_images(d['s'], n=3) if u]
            choices.append({'word': d['w'], 'display_word': d['w'], 'images': d_imgs, 'correct': False})
        random.shuffle(choices)
        rounds.append({'word': word, 'display_word': word, 'choices': choices})
    return rounds


@app.route('/api/vocab/level')
def vocab_level():
    lang = request.args.get('lang', 'en').strip()
    try:
        level = int(request.args.get('level', 1))
    except ValueError:
        level = 1
    mode = request.args.get('mode', 'easy').strip()
    if mode not in ('easy', 'challenge'):
        mode = 'easy'

    con = _vocab_conn()
    rows = con.execute(
        "SELECT id,lang,word,search,easy_json,hard_json FROM vocab_words WHERE lang=? AND level=?",
        (lang, level)
    ).fetchall()
    con.close()

    if not rows:
        return jsonify({'error': 'no words found for this level'}), 404

    selected = random.sample(rows, min(5, len(rows)))
    rounds = _build_rounds(selected, mode)
    return jsonify({'level': level, 'lang': lang, 'mode': mode, 'rounds': rounds})


@app.route('/api/vocab/generate-level', methods=['POST'])
def vocab_generate_level():
    import anthropic as _anthropic
    data = request.get_json(force=True, silent=True) or {}
    lang = data.get('lang', 'en')
    current_level = int(data.get('current_level', 1))
    seed_words = data.get('seed_words', [])
    next_level = current_level + 1

    con = _vocab_conn()
    existing = con.execute(
        "SELECT COUNT(*) FROM vocab_words WHERE lang=? AND level=?", (lang, next_level)
    ).fetchone()[0]

    if existing > 0:
        con.close()
        return jsonify({'level': next_level, 'words_added': 0, 'existed': True})

    lang_name = 'Spanish' if lang == 'es' else 'English'
    prompt = (
        f"You are building a vocabulary game for children ages 4-10. "
        f"Generate 10 concrete nouns in {lang_name} that are more advanced than: {', '.join(seed_words)}. "
        f"Return a JSON array of objects, each with: "
        f"word (the display word in {lang_name}), "
        f"search (English image search term for finding photos), "
        f"easy (array of 2 objects {{w, s}} where w is the distractor display word and s is its English image search term — choose very different objects), "
        f"hard (array of 2 objects {{w, s}} — choose similar objects in the same category as the word). "
        f"Return only the JSON array, no markdown."
    )

    try:
        client = _anthropic.Anthropic()
        msg = client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=2000,
            messages=[{'role': 'user', 'content': prompt}]
        )
        raw = msg.content[0].text.strip()
        # Strip markdown fences if present
        raw = re.sub(r'^```[a-z]*\n?', '', raw, flags=re.MULTILINE)
        raw = re.sub(r'\n?```$', '', raw, flags=re.MULTILINE)
        words = json.loads(raw)
    except Exception as e:
        con.close()
        return jsonify({'error': str(e)}), 500

    added = 0
    for w in words:
        try:
            easy_json = json.dumps(w.get('easy', []))
            hard_json = json.dumps(w.get('hard', []))
            cur = con.execute(
                "INSERT OR IGNORE INTO vocab_words (lang,level,word,search,easy_json,hard_json,source) VALUES (?,?,?,?,?,?,?)",
                (lang, next_level, w['word'], w['search'], easy_json, hard_json, 'ai')
            )
            added += cur.rowcount
        except Exception:
            pass
    con.commit()
    con.close()
    return jsonify({'level': next_level, 'words_added': added})


@app.route('/api/vocab/custom-sets', methods=['GET'])
def list_vocab_custom_sets():
    con = _vocab_conn()
    rows = con.execute("SELECT id, label, words_json FROM vocab_custom_sets").fetchall()
    con.close()
    sets = [{'id': r[0], 'label': r[1], 'words': json.loads(r[2])} for r in rows]
    return jsonify({'sets': sets})


@app.route('/api/vocab/custom-sets', methods=['POST'])
def create_vocab_custom_set():
    data = request.get_json(force=True, silent=True) or {}
    label = (data.get('label') or '').strip()
    words = data.get('words', [])

    if not label:
        return jsonify({'error': 'need a label'}), 400
    if len(words) < 2:
        return jsonify({'error': 'need at least 2 words'}), 400

    clean = []
    for w in words:
        if not isinstance(w, dict):
            continue
        word = (w.get('word') or '').strip()
        search = (w.get('search') or '').strip()
        easy = w.get('easy', [])
        hard = w.get('hard', [])
        if not word or not search:
            return jsonify({'error': f'word entry missing word or search'}), 400
        if len(easy) < 2 or len(hard) < 2:
            return jsonify({'error': f'"{word}" needs 2 easy and 2 hard distractors'}), 400
        images_raw = w.get('images') if isinstance(w.get('images'), dict) else None
        images = None
        if images_raw:
            norm = {}
            for slot, v in images_raw.items():
                if isinstance(v, list):
                    urls = [u for u in v if isinstance(u, str) and u]
                    if urls:
                        norm[slot] = urls
                elif isinstance(v, str) and v:
                    norm[slot] = [v]
            if norm:
                images = norm
        entry = {'word': word, 'search': search, 'easy': easy[:2], 'hard': hard[:2]}
        if images:
            entry['images'] = images
        clean.append(entry)

    con = _vocab_conn()
    base_id = _slugify(label)
    existing_ids = {r[0] for r in con.execute("SELECT id FROM vocab_custom_sets").fetchall()}
    set_id = base_id
    i = 2
    while set_id in existing_ids:
        set_id = f"{base_id}_{i}"
        i += 1

    con.execute(
        "INSERT INTO vocab_custom_sets (id, label, words_json) VALUES (?,?,?)",
        (set_id, label, json.dumps(clean))
    )
    con.commit()
    con.close()
    return jsonify({'id': set_id, 'label': label, 'words': clean}), 201


@app.route('/api/vocab/custom-sets/<set_id>', methods=['DELETE'])
def delete_vocab_custom_set(set_id):
    con = _vocab_conn()
    con.execute("DELETE FROM vocab_custom_sets WHERE id=?", (set_id,))
    con.commit()
    con.close()
    return '', 204


@app.route('/api/vocab/custom-set-round')
def vocab_custom_set_round():
    set_id = request.args.get('set_id', '').strip()
    mode = request.args.get('mode', 'easy').strip()
    if mode not in ('easy', 'challenge'):
        mode = 'easy'

    con = _vocab_conn()
    row = con.execute(
        "SELECT words_json FROM vocab_custom_sets WHERE id=?", (set_id,)
    ).fetchone()
    con.close()

    if not row:
        return jsonify({'error': 'custom set not found'}), 404

    words = json.loads(row[0])
    selected = random.sample(words, min(5, len(words)))

    def _get_imgs(search, picked):
        if picked:
            lst = picked if isinstance(picked, list) else [picked]
            result = [_cache_image(u) for u in lst if isinstance(u, str) and u]
            return [c for c in result if c]
        return [_cache_image(u) for u in _vocab_get_images(search, n=3) if u]

    rounds = []
    for w in selected:
        imgs = w.get('images') or {}
        mode_distractors = w['easy'] if mode == 'easy' else w['hard']
        d_keys = ['e1', 'e2'] if mode == 'easy' else ['h1', 'h2']

        target_imgs = _get_imgs(w['search'], imgs.get('target'))
        choices = [{'word': w['word'], 'display_word': w['word'], 'images': target_imgs, 'correct': True}]
        for d, dkey in zip(mode_distractors[:2], d_keys):
            d_imgs = _get_imgs(d['s'], imgs.get(dkey))
            choices.append({'word': d['w'], 'display_word': d['w'], 'images': d_imgs, 'correct': False})
        random.shuffle(choices)
        rounds.append({'word': w['word'], 'display_word': w['word'], 'choices': choices})

    return jsonify({'mode': mode, 'rounds': rounds})


# ── Vocab base word library ───────────────────────────────────────────────────

@app.route('/api/vocab/base-words')
def vocab_base_words():
    lang = request.args.get('lang', 'en').strip()
    if lang not in ('en', 'es'):
        lang = 'en'
    try:
        page = int(request.args.get('page', 0))
    except ValueError:
        page = 0
    con = _vocab_conn()
    rows = con.execute(
        "SELECT idx, word, search, images_json FROM vocab_base WHERE lang=? ORDER BY idx LIMIT 30 OFFSET ?",
        (lang, page * 30)
    ).fetchall()
    total = con.execute("SELECT COUNT(*) FROM vocab_base WHERE lang=?", (lang,)).fetchone()[0]
    con.close()
    words = [{'idx': r[0], 'word': r[1], 'search': r[2], 'images': json.loads(r[3])} for r in rows]
    total_pages = max(1, (total + 29) // 30)
    return jsonify({'words': words, 'total': total, 'page': page, 'total_pages': total_pages})


@app.route('/api/vocab/base-words/save-page', methods=['POST'])
def vocab_base_save_page():
    data = request.get_json(force=True, silent=True) or {}
    lang = data.get('lang', 'en').strip()
    if lang not in ('en', 'es'):
        return jsonify({'error': 'invalid lang'}), 400
    words = data.get('words', [])
    con = _vocab_conn()
    for w in words:
        try:
            idx = int(w['idx'])
        except (KeyError, ValueError, TypeError):
            continue
        word = (w.get('word') or '').strip()
        search = (w.get('search') or '').strip()
        images = w.get('images', [])
        if not isinstance(images, list):
            images = []
        images = [u for u in images if isinstance(u, str) and u]
        cached = [c for c in [_cache_image(u) for u in images] if c]
        con.execute(
            "UPDATE vocab_base SET word=?, search=?, images_json=? WHERE lang=? AND idx=?",
            (word, search, json.dumps(cached), lang, idx)
        )
    con.commit()
    con.close()
    return jsonify({'ok': True})


@app.route('/api/vocab/select-round', methods=['POST'])
def vocab_select_round():
    import anthropic as _anthropic
    data = request.get_json(force=True, silent=True) or {}
    lang = data.get('lang', 'en').strip()
    if lang not in ('en', 'es'):
        lang = 'en'
    mode = data.get('mode', 'easy').strip()
    if mode not in ('easy', 'challenge'):
        mode = 'easy'
    perf = data.get('perf', {})

    con = _vocab_conn()
    rows = con.execute(
        "SELECT word, search, images_json FROM vocab_base WHERE lang=? AND images_json != '[]'",
        (lang,)
    ).fetchall()
    con.close()

    if len(rows) < 6:
        return jsonify({'error': 'Not enough approved words. Open Custom Items Builder → Base Word Library and approve images first.'}), 400

    approved = [{'word': r[0], 'search': r[1], 'images': json.loads(r[2])} for r in rows]
    approved_list = ', '.join(w['word'] for w in approved)
    perf_lines = [
        f"{wd}: {p.get('correct',0)}/{p.get('attempts',0)} ({p.get('first_try',0)} 1st-try)"
        for wd, p in list(perf.items())[:60] if p.get('attempts', 0) > 0
    ]
    perf_str = '; '.join(perf_lines) if perf_lines else 'none yet'
    n = min(5, len(approved) // 2)

    prompt = (
        f"You are selecting words for a children's vocabulary image-matching game.\n"
        f"Language: {lang}. Mode: {mode} "
        f"({'very different distractors' if mode=='easy' else 'similar-looking distractors'}).\n"
        f"Approved words available: {approved_list}\n"
        f"Past performance: {perf_str}\n\n"
        f"Pick {n} target words. Prioritize unseen or low-accuracy words. "
        f"For each target pick 2 distractors from the approved list "
        f"({'very different objects' if mode=='easy' else 'visually similar objects'}).\n"
        f"Return ONLY a JSON array (no markdown):\n"
        f'[{{"target":"word","d1":"distractor1","d2":"distractor2"}}]'
    )

    try:
        client = _anthropic.Anthropic()
        msg = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=500,
            messages=[{'role': 'user', 'content': prompt}]
        )
        raw = msg.content[0].text.strip()
        raw = re.sub(r'^```[a-z]*\n?', '', raw, flags=re.MULTILINE)
        raw = re.sub(r'\n?```$', '', raw, flags=re.MULTILINE)
        selections = json.loads(raw)
    except Exception as e:
        return jsonify({'error': f'AI selection failed: {e}'}), 500

    word_map = {w['word']: w for w in approved}
    rounds = []
    for sel in selections[:n]:
        t = word_map.get(sel.get('target'))
        d1 = word_map.get(sel.get('d1'))
        d2 = word_map.get(sel.get('d2'))
        if not t or not d1 or not d2:
            continue
        choices = [
            {'word': t['word'], 'display_word': t['word'], 'images': t['images'], 'correct': True},
            {'word': d1['word'], 'display_word': d1['word'], 'images': d1['images'], 'correct': False},
            {'word': d2['word'], 'display_word': d2['word'], 'images': d2['images'], 'correct': False},
        ]
        random.shuffle(choices)
        rounds.append({'word': t['word'], 'display_word': t['word'], 'choices': choices})

    if not rounds:
        return jsonify({'error': 'Could not build rounds from AI selection.'}), 500
    return jsonify({'mode': mode, 'rounds': rounds})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
