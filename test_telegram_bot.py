#!/usr/bin/env python3
"""
Comprehensive Test Suite for NKHEKHE ALPHA Telegram Bot
========================================================
Tests all buttons, commands, callbacks, confirmations, and UX features.

Run: python3 /home/ubuntu/financial_orchestrator/test_telegram_bot.py
"""

import sys
import os
import json
import time
import tempfile
sys.path.insert(0, '/home/ubuntu/financial_orchestrator')

from datetime import datetime

# ═══════════════════════════════════════════════════════════════
# MOCK OBJECTS
# ═══════════════════════════════════════════════════════════════

class MockTradingEngine:
    """Simulates TradingBotIntegration for testing."""
    def __init__(self):
        self.running = True
        self.leverage = 75
        self.testnet = True
        self.symbol = 'BTCUSDT'
    
    def get_status(self):
        return {
            'running': self.running,
            'symbol': self.symbol,
            'price': 97500.00,
            'balance': 1500.00,
            'leverage': self.leverage,
            'testnet': self.testnet,
            'position': {
                'amount': 0.002,
                'entry_price': 97000.00,
                'unrealized_pnl': 10.00,
            },
            'wallet': {
                'total_unrealized_pnl': 10.00,
                'total_assets_value': 1510.00,
            }
        }
    
    def long(self, qty):
        return {
            'orderId': '12345',
            'order': {'orderId': '12345', 'symbol': 'BTCUSDT', 'executedQty': str(qty), 'avgPrice': '97500.00'},
            'leverage': self.leverage,
            'position': {'unrealized_pnl': 0}
        }
    
    def short(self, qty):
        return {
            'orderId': '12346',
            'order': {'orderId': '12346', 'symbol': 'BTCUSDT', 'executedQty': str(qty), 'avgPrice': '97500.00'},
            'leverage': self.leverage,
            'position': {'unrealized_pnl': 0}
        }
    
    def close(self):
        return {'orderId': '12347', 'message': 'Position closed', 'status': 'FILLED'}
    
    def start(self):
        self.running = True
        return {'success': True}
    
    def stop(self):
        self.running = False
        return {'success': True}
    
    def set_leverage(self, lev):
        self.leverage = lev
        return {'success': True, 'leverage': lev}
    
    def get_trade_history(self, limit=5):
        return [
            {'side': 'BUY', 'symbol': 'BTCUSDT', 'executedQty': '0.001', 'price': '97500'},
            {'side': 'SELL', 'symbol': 'BTCUSDT', 'executedQty': '0.001', 'price': '98000'},
        ]


class MockEventMonitor:
    """Simulates EventMonitor for testing."""
    def get_event_summary(self):
        return {
            'total_events': 15,
            'alert_counts': {'risk_alert': 3, 'error_event': 2, 'workflow_event': 5},
            'recent_events': [
                {'type': 'risk_alert', 'message': 'Position size warning', 'severity': 'warning'},
                {'type': 'error_event', 'message': 'Connection timeout', 'severity': 'error'},
            ]
        }


class MockBot:
    """Simulates TelegramWatchtower for testing."""
    def __init__(self):
        self.config = {
            'watchtower': {
                'name': 'Financial Orchestrator Watch Tower',
                'version': '1.0.0',
                'commands': []
            }
        }
        self.admin_chat_ids = {7361240735}
        self.trading_engine = MockTradingEngine()
        self.event_monitor = MockEventMonitor()
        
        # Import real components
        from telegram_watchtower.command_processor import CommandProcessor
        from telegram_watchtower.bot_menu import BotMenu
        
        self.command_processor = CommandProcessor(self.config)
        self.command_processor.set_trading_engine(self.trading_engine)
        self.bot_menu = BotMenu(self.config)
        
        self.sent_messages = []
        self.edited_messages = []
        self.callback_answers = []
    
    def send_message(self, chat_id, text, parse_mode='HTML', reply_markup=None):
        self.sent_messages.append({'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode})
    
    def send_keyboard(self, chat_id, text, keyboard, parse_mode='HTML'):
        self.sent_messages.append({'chat_id': chat_id, 'text': text, 'keyboard': keyboard, 'parse_mode': parse_mode})
    
    def edit_message_text(self, text, chat_id, parse_mode='HTML', reply_markup=None):
        self.edited_messages.append({'text': text, 'chat_id': chat_id, 'parse_mode': parse_mode})
    
    def answer_callback_query(self, callback_query_id, text=None):
        self.callback_answers.append({'id': callback_query_id, 'text': text})
    
    def get_status(self):
        return {
            'name': 'Financial Orchestrator Watch Tower',
            'version': '1.0.0',
            'status': 'running',
            'uptime_seconds': 3600,
            'alerts_count': 5,
        }
    
    def get_system_metrics(self):
        return {
            'memory': {'total_mb': 8192, 'used_mb': 4096, 'available_mb': 4096, 'usage_percent': 50.0},
            'uptime': '1h 30m',
        }


# ═══════════════════════════════════════════════════════════════
# TEST INFRASTRUCTURE
# ═══════════════════════════════════════════════════════════════

results = {'passed': 0, 'failed': 0, 'errors': [], 'skipped': 0}

def test(name: str):
    """Decorator for test functions."""
    def decorator(func):
        try:
            func()
            results['passed'] += 1
            print(f"  [PASS] {name}")
        except AssertionError as e:
            results['failed'] += 1
            results['errors'].append((name, str(e)))
            print(f"  [FAIL] {name}: {e}")
        except Exception as e:
            results['failed'] += 1
            results['errors'].append((name, f"Exception: {e}"))
            print(f"  [ERROR] {name}: {e}")
    return decorator

def assert_contains(text, substring, label=""):
    """Assert text contains substring."""
    assert substring in text, f"{label}: '{substring}' not found in response (first 200 chars: {text[:200]})"

def assert_html(text):
    """Assert text uses HTML formatting (not Markdown)."""
    # Should have HTML tags or no bold at all
    has_html = '<b>' in text or '<code>' in text or '<i>' in text
    has_markdown = '*bold*' in text or '_italic_' in text or '`code`' in text.replace('```', '')
    assert not has_markdown, f"Response uses Markdown instead of HTML: {text[:100]}"
    assert has_html or len(text) < 10, f"Response has no HTML formatting: {text[:100]}"

def assert_keyboard_has(keyboard, callback_data, label=""):
    """Assert keyboard contains a button with the given callback_data."""
    for row in keyboard:
        for button in row:
            if button.get('callback_data') == callback_data:
                return
    raise AssertionError(f"{label}: callback_data '{callback_data}' not found in keyboard")

def assert_keyboard_not_has(keyboard, callback_data, label=""):
    """Assert keyboard does NOT contain a button with the given callback_data."""
    for row in keyboard:
        for button in row:
            if button.get('callback_data') == callback_data:
                raise AssertionError(f"{label}: callback_data '{callback_data}' should not be in keyboard")

def setup_test_state_file():
    """Write a mock state file for testing."""
    state = {
        'timestamp': datetime.now().isoformat(),
        'running': True,
        'uptime': 3600,
        'price': 97500.00,
        'regime': 'bull',
        'strategy': 'momentum',
        'rsi': 65.5,
        'volatility': 'medium',
        'trend': 'up',
        'position_side': 'LONG',
        'position_amount': 0.002,
        'position_entry': 97000.00,
        'position_pnl': 10.00,
        'position_pnl_pct': 0.52,
        'balance': 1500.00,
        'leverage': 75,
        'testnet': True,
        'signal_action': 'buy',
        'signal_confidence': 0.82,
        'signal_ma': 'bullish',
        'learning_samples': 75,
        'learning_min_samples': 50,
        'learning_retrains': 3,
        'learning_trained': True,
        'daily_trades': 2,
        'daily_max_trades': 5,
        'daily_wins': 1,
        'daily_losses': 1,
        'daily_win_rate': 50.0,
        'daily_signals': 45,
        'daily_regime_stats': {},
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.05,
        'circuit_breaker_ok': True,
    }
    with open('/tmp/nkhekhe_dashboard_state.json', 'w') as f:
        json.dump(state, f)
    return state

def cleanup_test_state_file():
    """Remove test state file."""
    try:
        os.remove('/tmp/nkhekhe_dashboard_state.json')
    except:
        pass


# ═══════════════════════════════════════════════════════════════
# SETUP
# ═══════════════════════════════════════════════════════════════

print("=" * 60)
print("NKHEKHE ALPHA TELEGRAM BOT — TEST SUITE")
print("=" * 60)

# Create mock bot
bot = MockBot()
chat_id = 7361240735

# Write test state file
test_state = setup_test_state_file()

print(f"\n📁 State file: /tmp/nkhekhe_dashboard_state.json")
print(f"📊 Test state: price=${test_state['price']}, regime={test_state['regime']}, position={test_state['position_side']}")

# ═══════════════════════════════════════════════════════════════
# SECTION 1: TEXT COMMANDS (35 tests)
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SECTION 1: TEXT COMMANDS")
print("=" * 60)

# ── Dashboard commands ──

@test("/start returns welcome with dashboard state")
def _():
    result = bot.command_processor.process(chat_id, '/start', bot)
    assert_contains(result, 'NKHEKHE ALPHA')
    assert_contains(result, '97,500.00')  # price
    assert_contains(result, 'BULL')  # regime
    assert_contains(result, 'LONG')  # position
    assert_html(result)

@test("/hello returns welcome (alias)")
def _():
    result = bot.command_processor.process(chat_id, '/hello', bot)
    assert_contains(result, 'NKHEKHE ALPHA')
    assert_html(result)

@test("/menu returns dashboard header")
def _():
    result = bot.command_processor.process(chat_id, '/menu', bot)
    assert_contains(result, 'NKHEKHE ALPHA')
    assert_contains(result, 'DASHBOARD')
    assert_html(result)

@test("/dashboard returns quick summary")
def _():
    result = bot.command_processor.process(chat_id, '/dashboard', bot)
    assert_contains(result, 'QUICK DASHBOARD')
    assert_contains(result, '97,500.00')
    assert_contains(result, 'BULL')
    assert_contains(result, 'LONG')
    assert_html(result)

@test("/dash alias returns quick summary")
def _():
    result = bot.command_processor.process(chat_id, '/dash', bot)
    assert_contains(result, 'QUICK DASHBOARD')
    assert_html(result)

@test("/intel returns intelligence view")
def _():
    result = bot.command_processor.process(chat_id, '/intel', bot)
    assert_contains(result, 'AI INTELLIGENCE')
    assert_contains(result, 'momentum')  # strategy
    assert_contains(result, '65.5')  # RSI
    assert_contains(result, '82%')  # confidence
    assert_html(result)

@test("/portfolio returns portfolio view")
def _():
    result = bot.command_processor.process(chat_id, '/portfolio', bot)
    assert_contains(result, 'PORTFOLIO DASHBOARD')
    assert_contains(result, '0.002')  # position amount
    assert_contains(result, '97,000.00')  # entry
    assert_html(result)

@test("/market returns market data")
def _():
    result = bot.command_processor.process(chat_id, '/market', bot)
    assert_contains(result, 'MARKET DATA')
    assert_contains(result, '97,500.00')
    assert_contains(result, '65.5')
    assert_html(result)

@test("/risk returns risk status")
def _():
    result = bot.command_processor.process(chat_id, '/risk', bot)
    assert_contains(result, 'RISK STATUS')
    assert_contains(result, '2/5')  # trades
    assert_contains(result, 'LOW')  # risk level
    assert_html(result)

# ── System commands ──

@test("/status returns system status")
def _():
    result = bot.command_processor.process(chat_id, '/status', bot)
    assert_contains(result, 'SYSTEM STATUS')
    assert_contains(result, 'running')
    assert_html(result)

@test("/s alias returns system status")
def _():
    result = bot.command_processor.process(chat_id, '/s', bot)
    assert_contains(result, 'SYSTEM STATUS')
    assert_html(result)

@test("/sys returns quick status")
def _():
    result = bot.command_processor.process(chat_id, '/sys', bot)
    assert_contains(result, 'QUICK STATUS')
    assert_html(result)

@test("/metrics returns system metrics")
def _():
    result = bot.command_processor.process(chat_id, '/metrics', bot)
    assert_contains(result, 'SYSTEM METRICS')
    assert_contains(result, '50.0%')  # memory usage
    assert_html(result)

@test("/m alias returns metrics")
def _():
    result = bot.command_processor.process(chat_id, '/m', bot)
    assert_contains(result, 'SYSTEM METRICS')
    assert_html(result)

@test("/alerts returns alert summary")
def _():
    result = bot.command_processor.process(chat_id, '/alerts', bot)
    assert_contains(result, 'RECENT ALERTS')
    assert_contains(result, '15')  # total events
    assert_html(result)

@test("/a alias returns alerts")
def _():
    result = bot.command_processor.process(chat_id, '/a', bot)
    assert_contains(result, 'RECENT ALERTS')
    assert_html(result)

@test("/workflows returns workflow info")
def _():
    result = bot.command_processor.process(chat_id, '/workflows', bot)
    assert_contains(result, 'ACTIVE WORKFLOWS')
    assert_html(result)

@test("/wf alias returns workflows")
def _():
    result = bot.command_processor.process(chat_id, '/wf', bot)
    assert_contains(result, 'ACTIVE WORKFLOWS')
    assert_html(result)

@test("/agents returns agent info")
def _():
    result = bot.command_processor.process(chat_id, '/agents', bot)
    assert_contains(result, 'AGENT STATUS')
    assert_html(result)

@test("/ag alias returns agents")
def _():
    result = bot.command_processor.process(chat_id, '/ag', bot)
    assert_contains(result, 'AGENT STATUS')
    assert_html(result)

@test("/logs returns log info")
def _():
    result = bot.command_processor.process(chat_id, '/logs', bot)
    assert_contains(result, 'RECENT LOGS')
    assert_html(result)

@test("/help returns help message")
def _():
    result = bot.command_processor.process(chat_id, '/help', bot)
    assert_contains(result, 'Bot Commands')
    assert_contains(result, '/dashboard')
    assert_contains(result, '/long')
    assert_contains(result, '/short')
    assert_contains(result, '/close')
    assert_contains(result, '/systemon')
    assert_contains(result, '/systemoff')
    assert_html(result)

@test("/h alias returns help")
def _():
    result = bot.command_processor.process(chat_id, '/h', bot)
    assert_contains(result, 'Bot Commands')
    assert_html(result)

# ── Trading commands ──

@test("/long opens LONG position")
def _():
    result = bot.command_processor.process(chat_id, '/long 0.001', bot)
    assert_contains(result, 'LONG OPENED')
    assert_contains(result, '12345')
    assert_contains(result, '0.001')
    assert_html(result)

@test("/short opens SHORT position")
def _():
    result = bot.command_processor.process(chat_id, '/short 0.001', bot)
    assert_contains(result, 'SHORT OPENED')
    assert_contains(result, '12346')
    assert_html(result)

@test("/balance shows wallet balance")
def _():
    result = bot.command_processor.process(chat_id, '/balance', bot)
    assert_contains(result, 'WALLET BALANCE')
    assert_contains(result, '1,500.00')
    assert_html(result)

@test("/positions shows open positions")
def _():
    result = bot.command_processor.process(chat_id, '/positions', bot)
    assert_contains(result, 'OPEN POSITION')
    assert_contains(result, 'LONG')
    assert_html(result)

@test("/leverage shows current leverage")
def _():
    result = bot.command_processor.process(chat_id, '/leverage', bot)
    assert_contains(result, '75x')
    assert_html(result)

@test("/signal shows trading signal")
def _():
    result = bot.command_processor.process(chat_id, '/signal', bot)
    assert_contains(result, 'TRADING SIGNAL')
    assert_contains(result, '97,500.00')
    assert_html(result)

@test("/history shows trade history")
def _():
    result = bot.command_processor.process(chat_id, '/history', bot)
    assert_contains(result, 'TRADE HISTORY')
    assert_contains(result, 'BTCUSDT')
    assert_html(result)

@test("/trade shows trading status")
def _():
    result = bot.command_processor.process(chat_id, '/trade', bot)
    assert_contains(result, 'TRADING ENGINE')
    assert_contains(result, 'Running')
    assert_html(result)

@test("/futures shows trading status (alias)")
def _():
    result = bot.command_processor.process(chat_id, '/futures', bot)
    assert_contains(result, 'TRADING ENGINE')
    assert_html(result)

@test("/close handles close attempt")
def _():
    result = bot.command_processor.process(chat_id, '/close', bot)
    # Either closes successfully or reports no position / failed
    assert 'CLOSED' in result or 'close' in result.lower() or 'No position' in result or 'Failed' in result

@test("Unknown command returns error with help hint")
def _():
    result = bot.command_processor.process(chat_id, '/unknowncommand', bot)
    assert_contains(result, 'Unknown command')
    assert_contains(result, '/help')


# ═══════════════════════════════════════════════════════════════
# SECTION 2: CALLBACK HANDLERS (25 tests)
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SECTION 2: CALLBACK HANDLERS")
print("=" * 60)

@test("Dashboard Portfolio callback shows portfolio view")
def _():
    result = bot.bot_menu.handle_callback('dash_portfolio', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'PORTFOLIO DASHBOARD')
    assert_contains(msg, '97,500.00')
    assert keyboard is not None

@test("Dashboard Intelligence callback shows intel view")
def _():
    result = bot.bot_menu.handle_callback('dash_intel', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'AI INTELLIGENCE')
    assert_contains(msg, 'momentum')

@test("Dashboard Risk callback shows risk view")
def _():
    result = bot.bot_menu.handle_callback('dash_risk', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'RISK STATUS')
    assert_contains(msg, 'LOW')

@test("Main menu callback returns to dashboard")
def _():
    result = bot.bot_menu.handle_callback('main', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'NKHEKHE ALPHA DASHBOARD')
    assert keyboard is not None

@test("Trading menu callback shows trading sub-menu")
def _():
    result = bot.bot_menu.handle_callback('trading_menu', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'TRADING CONTROL')
    assert_contains(msg, '97,500.00')  # contextual price
    assert_contains(msg, 'LONG')  # position info

@test("System menu callback shows system sub-menu")
def _():
    result = bot.bot_menu.handle_callback('system_menu', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'SYSTEM CONTROL')
    assert_contains(msg, '1.0.0')  # version

@test("System On triggers confirmation dialog")
def _():
    result = bot.bot_menu.handle_callback('sys_on', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'START SYSTEM')
    assert_contains(msg, 'system')  # "Start all system components?"
    assert keyboard is not None
    assert_keyboard_has(keyboard, 'confirm_yes')
    assert_keyboard_has(keyboard, 'confirm_no')
    # Verify pending confirmation was stored
    assert chat_id in bot.bot_menu.pending_confirmations
    assert bot.bot_menu.pending_confirmations[chat_id] == 'sys_on'
    # Clean up
    bot.bot_menu.pending_confirmations.pop(chat_id, None)

@test("System Off triggers confirmation dialog")
def _():
    result = bot.bot_menu.handle_callback('sys_off', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'STOP SYSTEM')
    assert keyboard is not None
    assert_keyboard_has(keyboard, 'confirm_yes')
    assert_keyboard_has(keyboard, 'confirm_no')
    bot.bot_menu.pending_confirmations.pop(chat_id, None)

@test("Restart triggers confirmation dialog")
def _():
    result = bot.bot_menu.handle_callback('sys_restart', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'RESTART SYSTEM')
    assert keyboard is not None
    assert_keyboard_has(keyboard, 'confirm_yes')
    assert_keyboard_has(keyboard, 'confirm_no')
    bot.bot_menu.pending_confirmations.pop(chat_id, None)

@test("Trade Close triggers confirmation dialog")
def _():
    result = bot.bot_menu.handle_callback('trade_close', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'CLOSE POSITION')
    assert keyboard is not None
    assert_keyboard_has(keyboard, 'confirm_yes')
    assert_keyboard_has(keyboard, 'confirm_no')
    bot.bot_menu.pending_confirmations.pop(chat_id, None)

@test("Trade Stop triggers confirmation dialog")
def _():
    result = bot.bot_menu.handle_callback('trade_stop', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'STOP')  # "STOP TRADING" or "STOPPED"
    assert keyboard is not None
    assert_keyboard_has(keyboard, 'confirm_yes')
    assert_keyboard_has(keyboard, 'confirm_no')
    bot.bot_menu.pending_confirmations.pop(chat_id, None)

@test("Confirm Yes executes pending action")
def _():
    # Set up pending confirmation for trade_stop (more reliable)
    bot.bot_menu.pending_confirmations[chat_id] = 'trade_stop'
    result = bot.bot_menu.handle_callback('confirm_yes', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'STOPPED') or assert_contains(msg, 'stopped')
    # Pending should be cleared
    assert chat_id not in bot.bot_menu.pending_confirmations

@test("Confirm No cancels and returns to dashboard")
def _():
    bot.bot_menu.pending_confirmations[chat_id] = 'sys_on'
    result = bot.bot_menu.handle_callback('confirm_no', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'DASHBOARD')
    assert chat_id not in bot.bot_menu.pending_confirmations

@test("Trade LONG executes and returns None (send separately)")
def _():
    result = bot.bot_menu.handle_callback('trade_long', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'LONG OPENED')
    assert keyboard is None  # Should NOT edit the message

@test("Trade SHORT executes and returns separately")
def _():
    result = bot.bot_menu.handle_callback('trade_short', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'SHORT OPENED')
    assert keyboard is None

@test("Trade Balance returns balance info")
def _():
    result = bot.bot_menu.handle_callback('trade_balance', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'WALLET BALANCE')
    assert keyboard is None

@test("Trade Leverage returns leverage info")
def _():
    result = bot.bot_menu.handle_callback('trade_leverage', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, '75x')
    assert keyboard is None

@test("Trade Positions returns position info")
def _():
    result = bot.bot_menu.handle_callback('trade_positions', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'OPEN POSITION')
    assert keyboard is None

@test("Trade Signal returns signal info")
def _():
    result = bot.bot_menu.handle_callback('trade_signal', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'TRADING SIGNAL')
    assert keyboard is None

@test("Trade History returns history")
def _():
    result = bot.bot_menu.handle_callback('trade_history', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'TRADE HISTORY')
    assert keyboard is None

@test("Trade Status refreshes status")
def _():
    result = bot.bot_menu.handle_callback('trade_status', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'TRADING ENGINE')
    assert keyboard is None

@test("Trade Start starts engine")
def _():
    result = bot.bot_menu.handle_callback('trade_start', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'TRADING ENGINE STARTED')
    assert keyboard is None

@test("System Status returns system info")
def _():
    result = bot.bot_menu.handle_callback('st_quick', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'QUICK STATUS')
    assert keyboard is None

@test("Alerts returns alert info")
def _():
    result = bot.bot_menu.handle_callback('info_alerts', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'RECENT ALERTS')
    assert keyboard is None

@test("Hide menu returns hide message")
def _():
    result = bot.bot_menu.handle_callback('hide', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'Menu hidden')
    assert keyboard is None


# ═══════════════════════════════════════════════════════════════
# SECTION 3: CROSS-NAVIGATION (6 tests)
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SECTION 3: CROSS-NAVIGATION")
print("=" * 60)

@test("Portfolio → Intelligence navigation")
def _():
    result = bot.bot_menu.handle_callback('nav_intel', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'AI INTELLIGENCE')
    assert keyboard is not None

@test("Intelligence → Risk navigation")
def _():
    result = bot.bot_menu.handle_callback('nav_risk', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'RISK STATUS')

@test("Risk → Trading navigation")
def _():
    result = bot.bot_menu.handle_callback('nav_trading', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'TRADING CONTROL')

@test("Trading → System navigation")
def _():
    result = bot.bot_menu.handle_callback('nav_system', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'SYSTEM CONTROL')

@test("System → Dashboard navigation")
def _():
    result = bot.bot_menu.handle_callback('main', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'DASHBOARD')

@test("Refresh Portfolio reloads data")
def _():
    result = bot.bot_menu.handle_callback('refresh_portfolio', chat_id, bot)
    assert result is not None
    msg, keyboard = result
    assert_contains(msg, 'PORTFOLIO DASHBOARD')
    assert_contains(msg, '97,500.00')


# ═══════════════════════════════════════════════════════════════
# SECTION 4: STATE FORMATTING (4 tests)
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SECTION 4: STATE FORMATTING")
print("=" * 60)

@test("Main menu formats correctly with state data")
def _():
    msg, keyboard = bot.bot_menu.format_main_menu()
    assert_contains(msg, '97,500.00')
    assert_contains(msg, 'BULL')
    assert_contains(msg, 'BUY')
    assert_contains(msg, 'LONG')
    assert_contains(msg, '1,500.00')
    assert keyboard is not None
    assert len(keyboard) == 4  # 4 rows of buttons

@test("Portfolio view formats all position data")
def _():
    msg, keyboard = bot.bot_menu.format_portfolio_view()
    assert_contains(msg, '0.002')  # size
    assert_contains(msg, '97,000.00')  # entry
    assert_contains(msg, '97,500.00')  # current
    assert_contains(msg, '10.00')  # PnL
    assert_contains(msg, '50.0%')  # win rate
    assert keyboard is not None

@test("Intelligence view formats AI model data")
def _():
    msg, keyboard = bot.bot_menu.format_intelligence_view()
    assert_contains(msg, 'momentum')  # strategy
    assert_contains(msg, 'Trained')  # model status
    assert_contains(msg, '75/50')  # samples
    assert_contains(msg, '82%')  # confidence
    assert keyboard is not None

@test("Risk view calculates exposure correctly")
def _():
    msg, keyboard = bot.bot_menu.format_risk_view()
    assert_contains(msg, '2/5')  # trades
    assert_contains(msg, '-2.0%')  # stop loss
    assert_contains(msg, '+5.0%')  # take profit
    assert_contains(msg, 'LOW')  # risk level
    assert keyboard is not None


# ═══════════════════════════════════════════════════════════════
# SECTION 5: ERROR PATHS (5 tests)
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SECTION 5: ERROR PATHS")
print("=" * 60)

@test("No state file: main menu shows waiting message")
def _():
    cleanup_test_state_file()
    msg, keyboard = bot.bot_menu.format_main_menu()
    assert_contains(msg, 'Waiting for trading data')
    assert keyboard is not None
    # Restore state
    setup_test_state_file()

@test("Unknown callback returns None")
def _():
    result = bot.bot_menu.handle_callback('unknown_action_xyz', chat_id, bot)
    # Should return None (no response)
    assert result is None

@test("Trading command without engine returns error")
def _():
    old_engine = bot.command_processor.trading_engine
    bot.command_processor.trading_engine = None
    result = bot.command_processor.cmd_long(chat_id, '/long 0.001', bot)
    assert_contains(result, 'not initialized')
    bot.command_processor.trading_engine = old_engine

@test("Help command works without state file")
def _():
    cleanup_test_state_file()
    result = bot.command_processor.cmd_help(chat_id, '/help', bot)
    assert_contains(result, 'Bot Commands')
    assert_html(result)
    setup_test_state_file()

@test("Feedback text provided for all known callbacks")
def _():
    from telegram_watchtower.bot_menu import CALLBACK_FEEDBACK
    for action in ['dash_portfolio', 'dash_intel', 'dash_risk', 'trading_menu',
                   'sys_on', 'trade_long', 'trade_close', 'main', 'hide']:
        feedback = bot.bot_menu.get_callback_feedback(action)
        assert feedback is not None and len(feedback) > 0, f"No feedback for {action}"


# ═══════════════════════════════════════════════════════════════
# SECTION 6: HTML FORMATTING (3 tests)
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SECTION 6: HTML FORMATTING CONSISTENCY")
print("=" * 60)

@test("All command_processor commands use HTML, not Markdown")
def _():
    # Test a sample of commands
    for cmd in ['/dashboard', '/intel', '/portfolio', '/risk', '/help', '/status',
                '/metrics', '/alerts', '/long', '/balance', '/trade']:
        result = bot.command_processor.process(chat_id, cmd, bot)
        assert_html(result)

@test("No Markdown bold (*bold*) in any command response")
def _():
    for cmd in ['/start', '/dashboard', '/intel', '/portfolio', '/market', '/risk',
                '/status', '/sys', '/metrics', '/alerts', '/help', '/long', '/short',
                '/balance', '/positions', '/signal', '/history', '/trade']:
        result = bot.command_processor.process(chat_id, cmd, bot)
        assert '*bold*' not in result, f"Markdown bold found in {cmd}"
        assert '_italic_' not in result, f"Markdown italic found in {cmd}"

@test("All menu views use HTML formatting")
def _():
    msg, _ = bot.bot_menu.format_main_menu()
    assert '<b>' in msg
    msg, _ = bot.bot_menu.format_portfolio_view()
    assert '<b>' in msg
    msg, _ = bot.bot_menu.format_intelligence_view()
    assert '<b>' in msg
    msg, _ = bot.bot_menu.format_risk_view()
    assert '<b>' in msg


# ═══════════════════════════════════════════════════════════════
# SECTION 7: KEYBOARD DESIGN (3 tests)
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SECTION 7: KEYBOARD DESIGN")
print("=" * 60)

@test("Main menu keyboard has correct structure")
def _():
    kb = bot.bot_menu.get_main_menu_keyboard()
    assert len(kb) == 4, f"Expected 4 rows, got {len(kb)}"
    # Row 1: Portfolio, Intelligence, Risk
    assert len(kb[0]) == 3
    assert_keyboard_has(kb, 'dash_portfolio')
    assert_keyboard_has(kb, 'dash_intel')
    assert_keyboard_has(kb, 'dash_risk')
    # Row 2: Trading, System, Alerts
    assert_keyboard_has(kb, 'trading_menu')
    assert_keyboard_has(kb, 'system_menu')
    assert_keyboard_has(kb, 'info_alerts')
    # Row 3: System On/Off/Restart
    assert_keyboard_has(kb, 'sys_on')
    assert_keyboard_has(kb, 'sys_off')
    assert_keyboard_has(kb, 'sys_restart')
    # Row 4: Hide
    assert_keyboard_has(kb, 'hide')

@test("Trading menu keyboard has correct structure")
def _():
    kb = bot.bot_menu.get_trading_menu_keyboard()
    assert len(kb) == 5, f"Expected 5 rows, got {len(kb)}"
    assert_keyboard_has(kb, 'trade_long')
    assert_keyboard_has(kb, 'trade_short')
    assert_keyboard_has(kb, 'trade_close')
    assert_keyboard_has(kb, 'trade_start')
    assert_keyboard_has(kb, 'trade_stop')
    assert_keyboard_has(kb, 'main')  # back to dashboard

@test("Confirmation keyboard has Yes/No buttons")
def _():
    kb = bot.bot_menu.get_confirmation_keyboard()
    assert len(kb) == 1
    assert len(kb[0]) == 2
    assert_keyboard_has(kb, 'confirm_yes')
    assert_keyboard_has(kb, 'confirm_no')


# ═══════════════════════════════════════════════════════════════
# SECTION 8: CALLBACK FEEDBACK (2 tests)
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("SECTION 8: CALLBACK FEEDBACK")
print("=" * 60)

@test("All critical callbacks have feedback text")
def _():
    critical_actions = ['main', 'dash_portfolio', 'dash_intel', 'dash_risk',
                        'trading_menu', 'system_menu', 'trade_long', 'trade_short',
                        'trade_close', 'trade_balance', 'sys_on', 'sys_off', 'hide',
                        'confirm_yes', 'confirm_no']
    for action in critical_actions:
        feedback = bot.bot_menu.get_callback_feedback(action)
        assert feedback is not None and len(feedback) > 0, f"Missing feedback for {action}"

@test("Feedback text is concise (under 40 chars)")
def _():
    from telegram_watchtower.bot_menu import CALLBACK_FEEDBACK
    for action, feedback in CALLBACK_FEEDBACK.items():
        assert len(feedback) <= 40, f"Feedback too long for {action}: '{feedback}'"


# ═══════════════════════════════════════════════════════════════
# CLEANUP
# ═══════════════════════════════════════════════════════════════

cleanup_test_state_file()

# ═══════════════════════════════════════════════════════════════
# RESULTS
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("TEST RESULTS")
print("=" * 60)
print(f"  ✅ Passed:  {results['passed']}")
print(f"  ❌ Failed:  {results['failed']}")
print(f"  ⏭  Skipped: {results['skipped']}")
print(f"  📊 Total:   {results['passed'] + results['failed'] + results['skipped']}")

if results['errors']:
    print(f"\n  FAILED TESTS:")
    for name, error in results['errors']:
        print(f"    ❌ {name}")
        print(f"       → {error}")

print()
if results['failed'] == 0:
    print("🎉 ALL TESTS PASSED!")
    sys.exit(0)
else:
    print(f"💥 {results['failed']} TEST(S) FAILED")
    sys.exit(1)
