import json
import os
import io
import base64
import re
import random
import urllib.request
import urllib.parse
from flask import Flask, render_template, send_from_directory, abort, request, jsonify

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, 'settings.json')

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
]

# Only files explicitly registered above can be served
_ALLOWED = {g['desktop'] for g in GAMES} | {g['mobile'] for g in GAMES}

# ── EMNIST inference (lazy-loaded) ────────────────────────────────────────────
_sess = None
_word_img_cache = {}  # word → image URL

def _get_sess():
    global _sess
    if _sess is None:
        try:
            import onnxruntime as ort
            model_path = os.path.join(BASE_DIR, 'models', 'emnist_letters.onnx')
            _sess = ort.InferenceSession(model_path)
        except Exception as e:
            raise RuntimeError(f"Could not load EMNIST model: {e}. Run fetch_model.py first.")
    return _sess


def _ddg_image(query):
    """Fetch first DDG image result for query. Returns URL string or ''."""
    if query in _word_img_cache:
        return _word_img_cache[query]
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; arcade/1.0)'}
        vqd_url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}&ia=images"
        req = urllib.request.Request(vqd_url, headers=headers)
        html = urllib.request.urlopen(req, timeout=6).read().decode('utf-8', errors='ignore')
        m = re.search(r'vqd=([^&"\'>\s]+)', html)
        if not m:
            return ''
        vqd = m.group(1)
        api_url = (
            "https://duckduckgo.com/i.js?l=us-en&o=json"
            f"&q={urllib.parse.quote(query)}&vqd={vqd}&f=,,,,,&p=1"
        )
        req2 = urllib.request.Request(api_url, headers=headers)
        data = json.loads(urllib.request.urlopen(req2, timeout=6).read())
        url = data['results'][0]['image']
        _word_img_cache[query] = url
        return url
    except Exception:
        return ''


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html', games=GAMES)


@app.route('/games/<path:filename>')
def serve_game(filename):
    if filename not in _ALLOWED:
        abort(404)
    return send_from_directory(BASE_DIR, filename)


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


@app.route('/api/letter-words')
def letter_words():
    """Return a random word + DDG image URL for the given letter."""
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
    """Run EMNIST inference on a base64-encoded canvas PNG."""
    import numpy as np
    from PIL import Image

    data = request.get_json(force=True)
    if not data or 'image' not in data:
        return jsonify({'error': 'missing image'}), 400

    # Decode base64 PNG from canvas.toDataURL('image/png')
    header, b64 = data['image'].split(',', 1)
    img_bytes = base64.b64decode(b64)
    img = Image.open(io.BytesIO(img_bytes)).convert('L')  # grayscale

    # Crop to bounding box of ink, then resize to 28×28
    arr_full = __import__('numpy').array(img)
    # Find rows/cols with dark pixels (ink is dark on white canvas)
    dark = arr_full < 200
    rows = dark.any(axis=1)
    cols = dark.any(axis=0)
    if rows.any() and cols.any():
        r0, r1 = rows.argmax(), len(rows) - rows[::-1].argmax()
        c0, c1 = cols.argmax(), len(cols) - cols[::-1].argmax()
        pad = max((r1 - r0), (c1 - c0)) // 6
        r0 = max(0, r0 - pad); r1 = min(arr_full.shape[0], r1 + pad)
        c0 = max(0, c0 - pad); c1 = min(arr_full.shape[1], c1 + pad)
        cropped = img.crop((c0, r0, c1, r1))
        # Pad to square
        w, h = cropped.size
        side = max(w, h)
        square = Image.new('L', (side, side), 255)
        square.paste(cropped, ((side - w) // 2, (side - h) // 2))
        img = square

    arr = np.array(img.resize((28, 28), Image.LANCZOS), dtype=np.float32)
    # Invert: EMNIST expects white letter on black background
    arr = 1.0 - arr / 255.0
    # EMNIST images are transposed relative to how we draw — rotate 90° + flip
    arr = np.rot90(arr, k=3)          # rotate CCW 270° = CW 90°
    arr = np.fliplr(arr)
    arr = arr.reshape(1, 1, 28, 28)   # NCHW

    sess = _get_sess()
    out = sess.run(None, {sess.get_inputs()[0].name: arr})[0][0]
    ex = np.exp(out - out.max())
    probs = (ex / ex.sum()).tolist()
    top3 = sorted(enumerate(probs), key=lambda x: -x[1])[:3]

    return jsonify({
        'letter': chr(65 + top3[0][0]),
        'confidence': round(top3[0][1], 4),
        'top3': [{'letter': chr(65 + i), 'prob': round(p, 4)} for i, p in top3],
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
