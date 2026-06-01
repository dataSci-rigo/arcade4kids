import os
from flask import Flask, render_template, send_from_directory, abort

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

GAMES = [
    {
        'key':      'racer',
        'title':    'ENDLESS RUNNER',
        'desc':     ['3 THEMES · DODGE OBSTACLES', 'SURVIVE THE TUNNEL'],
        'desktop':  'racer.html',
        'mobile':   'racer_mobile.html',
        'color':    '#44ee44',
        'stripe':   'linear-gradient(90deg,#33cc33,#ffdd00)',
    },
    {
        'key':      'maze',
        'title':    'MAZE MUNCHER',
        'desc':     ['EAT DOTS · BEAT THE CLOCK', 'FIND THE EXIT'],
        'desktop':  'maze_muncher.html',
        'mobile':   'maze_muncher_mobile.html',
        'color':    '#00ccff',
        'stripe':   'linear-gradient(90deg,#0066ff,#00ccff)',
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
