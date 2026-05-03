#!/usr/bin/env python3
"""
SwiftDeploy HTTP Service
Supports stable and canary modes with chaos engineering endpoints
"""

import os
import json
import time
import random
from datetime import datetime
from flask import Flask, request, jsonify, Response

# Initialize Flask app
app = Flask(__name__)

# Configuration from environment
MODE = os.getenv('MODE', 'stable')
APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
APP_PORT = int(os.getenv('APP_PORT', 3000))

# Chaos state (for chaos endpoint)
chaos_state = {
    'active': False,
    'mode': None,
    'duration': None,
    'start_time': None,
    'error_rate': 0.0,
    'slow_duration': 0
}

# App state
app_state = {
    'start_time': time.time(),
    'request_count': 0
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_server_timestamp():
    """Return ISO8601 formatted timestamp"""
    return datetime.utcnow().isoformat() + 'Z'

def get_uptime():
    """Return uptime in seconds"""
    return int(time.time() - app_state['start_time'])

def add_mode_headers(response):
    """Add mode-specific headers"""
    if MODE == 'canary':
        response.headers['X-Mode'] = 'canary'
    response.headers['X-Deployed-By'] = 'swiftdeploy'
    return response

def should_chaos_error():
    """Check if we should return 500 based on error_rate"""
    if not chaos_state['active'] or chaos_state['mode'] != 'error':
        return False
    if random.random() < chaos_state['error_rate']:
        return True
    return False

def should_chaos_slow():
    """Check if we should apply slow response"""
    if not chaos_state['active'] or chaos_state['mode'] != 'slow':
        return False
    
    # Check if duration has elapsed
    if chaos_state['start_time']:
        elapsed = time.time() - chaos_state['start_time']
        if elapsed < chaos_state['slow_duration']:
            return True
        else:
            # Duration expired, recover
            chaos_state['active'] = False
            chaos_state['mode'] = None
    
    return False

def check_chaos_expired():
    """Check and clear expired chaos"""
    if not chaos_state['active']:
        return
    
    if chaos_state['mode'] == 'slow' and chaos_state['start_time']:
        elapsed = time.time() - chaos_state['start_time']
        if elapsed >= chaos_state['slow_duration']:
            chaos_state['active'] = False
            chaos_state['mode'] = None

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/', methods=['GET'])
def welcome():
    """
    GET / - Welcome endpoint
    Returns welcome message with mode, version, and server timestamp
    """
    app_state['request_count'] += 1
    
    response_data = {
        "message": "Welcome to SwiftDeploy API",
        "mode": MODE,
        "version": APP_VERSION,
        "timestamp": get_server_timestamp(),
        "uptime_seconds": get_uptime(),
        "request_count": app_state['request_count']
    }
    
    response = jsonify(response_data)
    return add_mode_headers(response), 200

@app.route('/healthz', methods=['GET'])
def healthz():
    """
    GET /healthz - Health check endpoint
    Returns status and process uptime in seconds
    Used by Docker health checks and monitoring
    """
    app_state['request_count'] += 1
    
    response_data = {
        "status": "healthy",
        "uptime_seconds": get_uptime(),
        "mode": MODE,
        "timestamp": get_server_timestamp()
    }
    
    response = jsonify(response_data)
    return add_mode_headers(response), 200

@app.route('/chaos', methods=['POST'])
def chaos():
    """
    POST /chaos - Chaos engineering endpoint
    Only available in canary mode
    
    Accepts:
    { "mode": "slow", "duration": N }    # Sleep N seconds
    { "mode": "error", "rate": 0.5 }     # Return 500 on 50% of requests
    { "mode": "recover" }                 # Cancel chaos
    """
    
    # Only allow chaos in canary mode
    if MODE != 'canary':
        response = jsonify({
            "error": "Chaos endpoint only available in canary mode",
            "current_mode": MODE
        })
        return add_mode_headers(response), 403
    
    app_state['request_count'] += 1
    
    try:
        data = request.get_json()
        
        if not data:
            return add_mode_headers(jsonify({
                "error": "Request body required"
            })), 400
        
        chaos_mode = data.get('mode')
        
        # ===== SLOW MODE =====
        if chaos_mode == 'slow':
            duration = data.get('duration', 5)
            chaos_state['active'] = True
            chaos_state['mode'] = 'slow'
            chaos_state['slow_duration'] = duration
            chaos_state['start_time'] = time.time()
            
            response = jsonify({
                "status": "chaos activated",
                "mode": "slow",
                "duration": duration,
                "timestamp": get_server_timestamp()
            })
            return add_mode_headers(response), 200
        
        # ===== ERROR MODE =====
        elif chaos_mode == 'error':
            rate = data.get('rate', 0.5)
            if not (0 <= rate <= 1):
                return add_mode_headers(jsonify({
                    "error": "Rate must be between 0 and 1"
                })), 400
            
            chaos_state['active'] = True
            chaos_state['mode'] = 'error'
            chaos_state['error_rate'] = rate
            chaos_state['start_time'] = time.time()
            
            response = jsonify({
                "status": "chaos activated",
                "mode": "error",
                "error_rate": rate,
                "timestamp": get_server_timestamp()
            })
            return add_mode_headers(response), 200
        
        # ===== RECOVER MODE =====
        elif chaos_mode == 'recover':
            chaos_state['active'] = False
            chaos_state['mode'] = None
            chaos_state['error_rate'] = 0.0
            chaos_state['slow_duration'] = 0
            
            response = jsonify({
                "status": "recovered",
                "mode": "normal",
                "timestamp": get_server_timestamp()
            })
            return add_mode_headers(response), 200
        
        else:
            return add_mode_headers(jsonify({
                "error": "Unknown chaos mode. Use: slow, error, recover"
            })), 400
    
    except Exception as e:
        return add_mode_headers(jsonify({
            "error": str(e)
        })), 500

# ============================================================================
# MIDDLEWARE FOR CHAOS INJECTION
# ============================================================================

@app.before_request
def chaos_middleware():
    """Apply chaos before processing request"""
    
    # Check if slow chaos is active
    if should_chaos_slow():
        print(f"[CHAOS] Slow mode: sleeping for {chaos_state['slow_duration']}s")
        time.sleep(chaos_state['slow_duration'])
    
    # Check if error chaos is active
    if should_chaos_error():
        print(f"[CHAOS] Error mode: returning 500 ({chaos_state['error_rate']*100}% rate)")
        response = jsonify({
            "error": "Simulated service error (chaos mode)",
            "mode": MODE,
            "timestamp": get_server_timestamp()
        })
        add_mode_headers(response)
        response.status_code = 500
        raise Exception("Chaos error injection")

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(Exception)
def handle_error(error):
    """Handle all exceptions"""
    response = jsonify({
        "error": str(error),
        "mode": MODE,
        "timestamp": get_server_timestamp()
    })
    add_mode_headers(response)
    response.status_code = 500
    return response

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    response = jsonify({
        "error": "Endpoint not found",
        "available_endpoints": ["/", "/healthz", "/chaos"]
    })
    add_mode_headers(response)
    response.status_code = 404
    return response

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == '__main__':
    print(f"🚀 SwiftDeploy Service Starting")
    print(f"   Mode: {MODE}")
    print(f"   Version: {APP_VERSION}")
    print(f"   Port: {APP_PORT}")
    print(f"   Endpoints: /, /healthz, /chaos")
    print()
    
    # Run Flask app
    # debug=False for production
    # host='0.0.0.0' to accept external connections
    app.run(
        host='0.0.0.0',
        port=APP_PORT,
        debug=False,
        use_reloader=False
    )
