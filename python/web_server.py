#!/usr/bin/env python3
from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__, 
            template_folder='../web/templates',
            static_folder='../web/static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/metrics')
def get_metrics():
    """Get current metrics"""
    try:
        with open('/tmp/rl_state.json', 'r') as f:
            return jsonify(json.load(f))
    except:
        return jsonify({'error': 'No data available'})

@app.route('/api/comparison')
def get_comparison():
    """Get baseline vs RL comparison"""
    # Read from results/live/comparison_latest.csv
    return jsonify({})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)