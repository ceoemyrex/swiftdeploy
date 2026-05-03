#!/usr/bin/env python3
"""SwiftDeploy HTTP Service"""

import os
import json
import time
from datetime import datetime
from flask import Flask, jsonify, request

app = Flask(__name__)

# Config
MODE = os.getenv('MODE', 'stable')
APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
APP_PORT = int(os.getenv('APP_PORT', 3000))

# State
start_time = time.time()
request_count = 0

@app.route('/')
def welcome():
    """Welcome endpoint"""
    return jsonify({
        "message": "Welcome to SwiftDeploy API",
        "mode": MODE,
        "version": APP_VERSION,
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "uptime_seconds": int(time.time() - start_time)
    }), 200

@app.route('/healthz')
def healthz():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "uptime_seconds": int(time.time() - start_time),
        "mode": MODE,
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    }), 200

@app.route('/chaos', methods=['POST'])
def chaos():
    """Chaos endpoint (canary only)"""
    if MODE != 'canary':
        return jsonify({"error": "Chaos only in canary mode"}), 403
    
    data = request.get_json()
    return jsonify({
        "status": "chaos activated",
        "mode": data.get('mode'),
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    }), 200

if __name__ == '__main__':
    print(f"🚀 Starting SwiftDeploy API")
    print(f"   Mode: {MODE}")
    print(f"   Port: {APP_PORT}")
    app.run(host='0.0.0.0', port=APP_PORT, debug=False)
