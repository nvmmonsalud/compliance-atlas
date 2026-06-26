"""
api_combined.py — Combined Flask app for Render deploy.

Serves:
  - Static landing page (public/) at /
  - Public JSON API at /api/* (summary, findings, conflicts, arbitrage, sectors, health)

Single-file Flask app, no external state, no DB.
On startup, the build command (python curate.py) generates data/public/*.json.
"""
import json
import os
import time
from flask import Flask, jsonify, send_from_directory, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=os.path.join(BASE_DIR, 'public'), static_url_path='')

DATA_DIR = os.path.join(BASE_DIR, 'data', 'public')
START_TIME = time.time()
_DATA = {}


def load_data():
    """Load all public JSON files into memory at startup."""
    global _DATA
    for name in ('summary', 'findings', 'conflicts', 'arbitrage', 'sectors'):
        path = os.path.join(DATA_DIR, f'{name}.json')
        if os.path.exists(path):
            with open(path) as f:
                _DATA[name] = json.load(f)
        else:
            _DATA[name] = None
            print(f'WARNING: {path} not found')


# === Static ===
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')


@app.route('/')
def index():
    return send_from_directory(PUBLIC_DIR, 'index.html')


@app.route('/og.png')
def og():
    return send_from_directory(PUBLIC_DIR, 'og.png')


@app.route('/REEL.md')
def reel():
    return send_from_directory(PUBLIC_DIR, 'REEL.md')


# === API ===
@app.route('/api/manifest')
def manifest():
    return jsonify({
        'name': 'Compliance Atlas Public API',
        'version': '1.0.0',
        'endpoints': ['/api/summary', '/api/findings', '/api/conflicts', '/api/arbitrage', '/api/sectors', '/api/health'],
    })


@app.route('/api/summary')
def api_summary():
    if _DATA.get('summary'):
        return jsonify(_DATA['summary'])
    return jsonify({'error': 'summary.json missing or empty'}), 500


@app.route('/api/findings')
def api_findings():
    findings = _DATA.get('findings') or []
    if isinstance(findings, dict):
        findings = findings.get('findings', [])
    total_unfiltered = len(findings)
    if request.args.get('severity'):
        findings = [f for f in findings if f.get('severity') == request.args['severity']]
    if request.args.get('jurisdiction'):
        findings = [f for f in findings if f.get('jurisdiction') == request.args['jurisdiction']]
    if request.args.get('sector'):
        findings = [f for f in findings if request.args['sector'] in (f.get('sectors') or [])]
    if request.args.get('limit'):
        try:
            findings = findings[:int(request.args['limit'])]
        except ValueError:
            pass
    return jsonify({
        'total_unfiltered': total_unfiltered,
        'count': len(findings),
        'findings': findings,
    })


@app.route('/api/conflicts')
def api_conflicts():
    if _DATA.get('conflicts'):
        return jsonify(_DATA['conflicts'])
    return jsonify({'error': 'conflicts.json missing'}), 500


@app.route('/api/arbitrage')
def api_arbitrage():
    if _DATA.get('arbitrage'):
        return jsonify(_DATA['arbitrage'])
    return jsonify({'error': 'arbitrage.json missing'}), 500


@app.route('/api/sectors')
def api_sectors():
    if _DATA.get('sectors'):
        return jsonify(_DATA['sectors'])
    return jsonify({'error': 'sectors.json missing'}), 500


@app.route('/api/health')
def api_health():
    findings_data = _DATA.get('findings') or []
    if isinstance(findings_data, dict):
        findings_loaded = len(findings_data.get('findings', []))
    else:
        findings_loaded = len(findings_data)
    return jsonify({
        'status': 'ok',
        'uptime_seconds': int(time.time() - START_TIME),
        'findings_loaded': findings_loaded,
        'version': '1.0.0',
    })


# === CORS — explicit preflight for the public API ===
@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


@app.route('/api/<path:_>', methods=['OPTIONS'])
def options(_):
    return ('', 204)


load_data()
print(f'🔓 Compliance Atlas API ready ({sum(1 for v in _DATA.values() if v)}/5 data files loaded)')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
