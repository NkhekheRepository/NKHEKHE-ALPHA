"""
Web Dashboard for Paper Trading
Layer 7: Command & Control - Web Interface
"""

import os
import sys
from pathlib import Path
from threading import Thread
from flask import Flask, render_template, jsonify, request
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))

from paper_trading.engine import PaperTradingEngine

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32)

engine: PaperTradingEngine = None
refresh_interval = 1


def create_app(trading_engine: PaperTradingEngine = None) -> Flask:
    """Create and configure Flask app."""
    global engine
    
    if trading_engine:
        engine = trading_engine
    
    return app


@app.route('/')
def index():
    """Main dashboard page."""
    config = {}
    if engine:
        config = engine.config
    
    return render_template('index.html', config=config)


@app.route('/api/status')
def api_status():
    """Get system status."""
    if engine is None:
        return jsonify({'error': 'Engine not initialized'}), 500
    
    status = engine.get_status()
    return jsonify(status)


@app.route('/api/positions')
def api_positions():
    """Get open positions."""
    if engine is None:
        return jsonify({'error': 'Engine not initialized'}), 500
    
    positions = engine.get_positions()
    return jsonify(positions)


@app.route('/api/pnl')
def api_pnl():
    """Get P&L data."""
    if engine is None:
        return jsonify({'error': 'Engine not initialized'}), 500
    
    status = engine.get_status()
    return jsonify({
        'daily_pnl': status.get('daily_pnl', 0),
        'capital': status.get('capital', 0),
        'leverage': status.get('leverage', 1)
    })


@app.route('/api/health')
def api_health():
    """Get health report."""
    if engine is None:
        return jsonify({'error': 'Engine not initialized'}), 500
    
    from paper_trading.layers.layer6_orchestration.health_monitor import health_monitor
    report = health_monitor.get_health_report()
    return jsonify(report)


@app.route('/api/regime')
def api_regime():
    """Get current market regime."""
    if engine is None:
        return jsonify({'error': 'Engine not initialized'}), 500
    
    status = engine.get_status()
    return jsonify({
        'regime': status.get('current_regime', 'unknown'),
        'strategy': status.get('active_strategy', 'unknown')
    })


@app.route('/api/start', methods=['POST'])
def api_start():
    """Start trading."""
    if engine is None:
        return jsonify({'error': 'Engine not initialized'}), 500
    
    if not engine.running:
        engine.start()
        return jsonify({'status': 'started'})
    return jsonify({'status': 'already_running'})


@app.route('/api/stop', methods=['POST'])
def api_stop():
    """Stop trading."""
    if engine is None:
        return jsonify({'error': 'Engine not initialized'}), 500
    
    if engine.running:
        engine.stop()
        return jsonify({'status': 'stopped'})
    return jsonify({'status': 'already_stopped'})


@app.route('/api/emergency', methods=['POST'])
def api_emergency():
    """Emergency stop."""
    if engine is None:
        return jsonify({'error': 'Engine not initialized'}), 500
    
    engine.emergency_stop()
    return jsonify({'status': 'emergency_stop'})


@app.route('/api/switch_strategy', methods=['POST'])
def api_switch_strategy():
    """Switch strategy."""
    if engine is None:
        return jsonify({'error': 'Engine not initialized'}), 500
    
    data = request.get_json()
    strategy_name = data.get('strategy')
    
    if engine.switch_strategy(strategy_name):
        return jsonify({'status': 'switched', 'strategy': strategy_name})
    
    return jsonify({'error': 'Strategy not found'}), 400


def run_dashboard(host: str = '0.0.0.0', port: int = 8080, 
                trading_engine: PaperTradingEngine = None):
    """Run the dashboard server."""
    global engine
    
    if trading_engine:
        engine = trading_engine
    
    logger.info(f"Starting dashboard on {host}:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)


def start_dashboard_thread(host: str = '0.0.0.0', port: int = 8080,
                          trading_engine: PaperTradingEngine = None):
    """Start dashboard in background thread."""
    thread = Thread(target=run_dashboard, 
                   args=(host, port, trading_engine),
                   daemon=True)
    thread.start()
    return thread


if __name__ == '__main__':
    print("=" * 50)
    print("Paper Trading Dashboard")
    print("=" * 50)
    print("\nStarting engine and dashboard...\n")
    
    try:
        engine = PaperTradingEngine()
        engine.start()
        
        run_dashboard('0.0.0.0', 8080, engine)
        
    except KeyboardInterrupt:
        print("\nShutting down...")
        if engine:
            engine.stop()
