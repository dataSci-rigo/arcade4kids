import json
import os
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
]

# Only files explicitly registered above can be served
_ALLOWED = {g['desktop'] for g in GAMES} | {g['mobile'] for g in GAMES}


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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
