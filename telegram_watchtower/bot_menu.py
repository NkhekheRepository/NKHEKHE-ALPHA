#!/usr/bin/env python3
"""
Bot Menu Module — Unified Telegram Dashboard
Provides inline keyboard menus and callback handlers for the NKHEKHE ALPHA bot.
"""

import logging
import json
import os
import time
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger('BotMenu')

# ─── State File Path ─────────────────────────────────────────────────────────────
STATE_FILE = '/tmp/nkhekhe_dashboard_state.json'

# ─── Callback Actions ────────────────────────────────────────────────────────────
CALLBACK_ACTIONS = {
    # Top-level
    'main_menu':      'main',
    'system_on':      'sys_on',
    'system_off':     'sys_off',
    'restart':        'sys_restart',
    'hide_menu':      'hide',
    # Dashboard sections
    'portfolio':      'dash_portfolio',
    'intelligence':   'dash_intel',
    'risk':           'dash_risk',
    # Trading
    'trading_menu':   'trading_menu',
    # System
    'system_menu':    'system_menu',
    'quick_status':   'st_quick',
    'detailed_status':'st_detailed',
    'metrics':        'st_metrics',
    'workflows':      'info_wf',
    'agents':         'info_ag',
    'logs':           'info_logs',
    'alerts':         'info_alerts',
    # Trading actions
    'trade_long':     'trade_long',
    'trade_short':    'trade_short',
    'trade_close':    'trade_close',
    'trade_balance':  'trade_balance',
    'trade_leverage': 'trade_leverage',
    'trade_positions':'trade_positions',
    'trade_signal':   'trade_signal',
    'trade_history':  'trade_history',
    'trade_status':   'trade_status',
    'trade_start':    'trade_start',
    'trade_stop':     'trade_stop',
    # Refresh actions
    'refresh_portfolio':    'refresh_portfolio',
    'refresh_intel':        'refresh_intel',
    'refresh_risk':         'refresh_risk',
    # Cross-navigation
    'nav_portfolio':        'nav_portfolio',
    'nav_intel':            'nav_intel',
    'nav_risk':             'nav_risk',
    'nav_trading':          'nav_trading',
    'nav_system':           'nav_system',
}


# ─── State Reader ──────────────────────────────────────────────────────────────
def load_dashboard_state() -> Optional[Dict]:
    """Load dashboard state from shared file. Returns None if unavailable."""
    try:
        if not os.path.exists(STATE_FILE):
            return None
        mtime = os.path.getmtime(STATE_FILE)
        if time.time() - mtime > 300:  # stale > 5 min
            return None
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"State read error: {e}")
        return None


# ─── Helpers ────────────────────────────────────────────────────────────────────
def _fmt_dollars(v: float) -> str:
    return f"${v:,.2f}"

def _fmt_pct(v: float) -> str:
    return f"{v:+.2f}%"

def _fmt_uptime(seconds: float) -> str:
    if not seconds:
        return "0m"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    return f"{h}h {m}m" if h else f"{m}m"

def _regime_emoji(r: str) -> str:
    return {'bull': '🐂', 'bear': '🐻', 'volatile': '⚡', 'sideways': '➡️'}.get(r, '❓')

def _action_emoji(a: str) -> str:
    return {'buy': '🟢', 'sell': '🔴', 'hold': '⏸️'}.get(a, '❓')


class BotMenu:
    def __init__(self, config: Dict):
        self.config = config

    # ═══════════════════════════════════════════════════════════════════════════
    # KEYBOARD DEFINITIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_main_menu_keyboard(self) -> List[List[Dict]]:
        """Unified dashboard main menu."""
        return [
            [
                {"text": "🤖 Portfolio",  "callback_data": CALLBACK_ACTIONS['portfolio']},
                {"text": "🧠 Intelligence","callback_data": CALLBACK_ACTIONS['intelligence']},
                {"text": "🛡️ Risk",       "callback_data": CALLBACK_ACTIONS['risk']},
            ],
            [
                {"text": "📈 Trading",    "callback_data": CALLBACK_ACTIONS['trading_menu']},
                {"text": "⚙️ System",     "callback_data": CALLBACK_ACTIONS['system_menu']},
                {"text": "🔔 Alerts",     "callback_data": CALLBACK_ACTIONS['alerts']},
            ],
            [
                {"text": "🟢 System On",  "callback_data": CALLBACK_ACTIONS['system_on']},
                {"text": "🔴 System Off", "callback_data": CALLBACK_ACTIONS['system_off']},
                {"text": "🔄 Restart",    "callback_data": CALLBACK_ACTIONS['restart']},
            ],
            [
                {"text": "🔒 Hide Menu",  "callback_data": CALLBACK_ACTIONS['hide_menu']},
            ],
        ]

    def get_portfolio_keyboard(self) -> List[List[Dict]]:
        return [
            [
                {"text": "🔄 Refresh",        "callback_data": CALLBACK_ACTIONS['refresh_portfolio']},
                {"text": "🧠 Intelligence",   "callback_data": CALLBACK_ACTIONS['nav_intel']},
                {"text": "🛡️ Risk",           "callback_data": CALLBACK_ACTIONS['nav_risk']},
            ],
            [
                {"text": "📈 Trading",        "callback_data": CALLBACK_ACTIONS['nav_trading']},
                {"text": "⚙️ System",         "callback_data": CALLBACK_ACTIONS['nav_system']},
            ],
            [
                {"text": "⬅️ Dashboard",      "callback_data": CALLBACK_ACTIONS['main_menu']},
            ],
        ]

    def get_intelligence_keyboard(self) -> List[List[Dict]]:
        return [
            [
                {"text": "🔄 Refresh",        "callback_data": CALLBACK_ACTIONS['refresh_intel']},
                {"text": "🤖 Portfolio",      "callback_data": CALLBACK_ACTIONS['nav_portfolio']},
                {"text": "🛡️ Risk",           "callback_data": CALLBACK_ACTIONS['nav_risk']},
            ],
            [
                {"text": "📈 Trading",        "callback_data": CALLBACK_ACTIONS['nav_trading']},
                {"text": "⚙️ System",         "callback_data": CALLBACK_ACTIONS['nav_system']},
            ],
            [
                {"text": "⬅️ Dashboard",      "callback_data": CALLBACK_ACTIONS['main_menu']},
            ],
        ]

    def get_risk_keyboard(self) -> List[List[Dict]]:
        return [
            [
                {"text": "🔄 Refresh",        "callback_data": CALLBACK_ACTIONS['refresh_risk']},
                {"text": "🤖 Portfolio",      "callback_data": CALLBACK_ACTIONS['nav_portfolio']},
                {"text": "🧠 Intelligence",   "callback_data": CALLBACK_ACTIONS['nav_intel']},
            ],
            [
                {"text": "📈 Trading",        "callback_data": CALLBACK_ACTIONS['nav_trading']},
                {"text": "⚙️ System",         "callback_data": CALLBACK_ACTIONS['nav_system']},
            ],
            [
                {"text": "⬅️ Dashboard",      "callback_data": CALLBACK_ACTIONS['main_menu']},
            ],
        ]

    def get_trading_menu_keyboard(self) -> List[List[Dict]]:
        return [
            [
                {"text": "📈 LONG",  "callback_data": "trade_long"},
                {"text": "📉 SHORT", "callback_data": "trade_short"},
                {"text": "🛑 CLOSE", "callback_data": "trade_close"},
            ],
            [
                {"text": "💰 Balance",   "callback_data": "trade_balance"},
                {"text": "⚡ Leverage",  "callback_data": "trade_leverage"},
                {"text": "📊 Positions", "callback_data": "trade_positions"},
            ],
            [
                {"text": "📈 Signal",    "callback_data": "trade_signal"},
                {"text": "📜 History",   "callback_data": "trade_history"},
                {"text": "🔄 Refresh",   "callback_data": "trade_status"},
            ],
            [
                {"text": "🟢 Live",      "callback_data": "trade_start"},
                {"text": "🔴 Stop",      "callback_data": "trade_stop"},
            ],
            [
                {"text": "⬅️ Dashboard", "callback_data": "main"},
            ],
        ]

    def get_system_menu_keyboard(self) -> List[List[Dict]]:
        return [
            [
                {"text": "📊 Status",   "callback_data": CALLBACK_ACTIONS['quick_status']},
                {"text": "📈 Metrics",  "callback_data": CALLBACK_ACTIONS['metrics']},
                {"text": "🔔 Alerts",   "callback_data": CALLBACK_ACTIONS['alerts']},
            ],
            [
                {"text": "📁 Workflows","callback_data": CALLBACK_ACTIONS['workflows']},
                {"text": "💻 Agents",   "callback_data": CALLBACK_ACTIONS['agents']},
                {"text": "📄 Logs",     "callback_data": CALLBACK_ACTIONS['logs']},
            ],
            [
                {"text": "⬅️ Dashboard","callback_data": CALLBACK_ACTIONS['main_menu']},
            ],
        ]

    # ═══════════════════════════════════════════════════════════════════════════
    # FORMATTERS
    # ═══════════════════════════════════════════════════════════════════════════

    def format_main_menu(self) -> Tuple[str, List[List[Dict]]]:
        state = load_dashboard_state()
        ts = datetime.now().strftime('%H:%M:%S')

        if not state:
            msg = (
                f"🤖 <b>NKHEKHE ALPHA DASHBOARD</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🕐 {ts}\n\n"
                f"⏳ <i>Waiting for trading data...\n"
                f"Start autonomous_trading.py to see live dashboard.</i>"
            )
            return msg, self.get_main_menu_keyboard()

        price = state.get('price', 0)
        regime = state.get('regime', 'unknown')
        position_side = state.get('position_side', 'FLAT')
        pnl_pct = state.get('position_pnl_pct', 0)
        daily_trades = state.get('daily_trades', 0)
        max_trades = state.get('daily_max_trades', 5)
        signal_action = state.get('signal_action', 'hold')
        signal_conf = state.get('signal_confidence', 0)
        balance = state.get('balance', 0)
        uptime = _fmt_uptime(state.get('uptime', 0))

        side_emoji = '📈' if position_side == 'LONG' else '📉' if position_side == 'SHORT' else '➡️'
        pnl_emoji = '🟢' if pnl_pct > 0 else '🔴' if pnl_pct < 0 else '⚪'

        msg = (
            f"🤖 <b>NKHEKHE ALPHA DASHBOARD</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🕐 {ts}  ⏱ {uptime}\n\n"
            f"📊 <b>MARKET</b>\n"
            f"├─ Price: {_fmt_dollars(price)}\n"
            f"├─ Regime: {_regime_emoji(regime)} {regime.upper()}\n"
            f"└─ Signal: {_action_emoji(signal_action)} {signal_action.upper()} ({signal_conf:.0%})\n\n"
            f"💼 <b>POSITION</b>\n"
            f"├─ {side_emoji} {position_side}\n"
            f"└─ PnL: {pnl_emoji} {_fmt_pct(pnl_pct)}\n\n"
            f"💰 <b>ACCOUNT</b>\n"
            f"├─ Balance: {_fmt_dollars(balance)}\n"
            f"└─ Trades: {daily_trades}/{max_trades}\n\n"
            f"<i>Tap a section below for details</i>"
        )
        return msg, self.get_main_menu_keyboard()

    def format_portfolio_view(self) -> Tuple[str, List[List[Dict]]]:
        state = load_dashboard_state()
        ts = datetime.now().strftime('%H:%M:%S')

        if not state:
            return f"🤖 <b>PORTFOLIO</b>\n━━━━━━━━━━━━━\n⏳ No data available.", self.get_portfolio_keyboard()

        position_side = state.get('position_side', 'FLAT')
        amount = state.get('position_amount', 0)
        entry = state.get('position_entry', 0)
        price = state.get('price', 0)
        pnl = state.get('position_pnl', 0)
        pnl_pct = state.get('position_pnl_pct', 0)
        balance = state.get('balance', 0)
        leverage = state.get('leverage', 75)
        daily_wins = state.get('daily_wins', 0)
        daily_losses = state.get('daily_losses', 0)
        win_rate = state.get('daily_win_rate', 0)
        daily_trades = state.get('daily_trades', 0)
        max_trades = state.get('daily_max_trades', 5)
        testnet = state.get('testnet', True)
        signal_action = state.get('signal_action', 'hold')
        signal_conf = state.get('signal_confidence', 0)

        side_emoji = '📈' if position_side == 'LONG' else '📉' if position_side == 'SHORT' else '➡️'
        pnl_emoji = '🟢' if pnl_pct > 0 else '🔴' if pnl_pct < 0 else '⚪'
        testnet_label = 'TESTNET' if testnet else 'LIVE'

        pos_size_usd = amount * price

        msg = (
            f"🤖 <b>PORTFOLIO DASHBOARD</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🕐 {ts}  |  {testnet_label}\n\n"
            f"📊 <b>POSITION</b>\n"
            f"├─ Side: {side_emoji} {position_side}\n"
            f"├─ Size: {amount:.4f} BTC ({_fmt_dollars(pos_size_usd)})\n"
            f"├─ Entry: {_fmt_dollars(entry)}\n"
            f"├─ Current: {_fmt_dollars(price)}\n"
            f"└─ PnL: {pnl_emoji} {_fmt_dollars(pnl)} ({_fmt_pct(pnl_pct)})\n\n"
            f"💰 <b>ACCOUNT</b>\n"
            f"├─ Balance: {_fmt_dollars(balance)}\n"
            f"├─ Leverage: {leverage}x\n"
            f"├─ Daily PnL: {_fmt_pct(pnl_pct if daily_trades > 0 else 0)}\n"
            f"├─ Win Rate: {win_rate:.1f}% ({daily_wins}W/{daily_losses}L)\n"
            f"└─ Trades Today: {daily_trades}/{max_trades}\n\n"
            f"📈 <b>CURRENT SIGNAL</b>\n"
            f"├─ Action: {_action_emoji(signal_action)} {signal_action.upper()}\n"
            f"└─ Confidence: {signal_conf:.0%}"
        )
        return msg, self.get_portfolio_keyboard()

    def format_intelligence_view(self) -> Tuple[str, List[List[Dict]]]:
        state = load_dashboard_state()
        ts = datetime.now().strftime('%H:%M:%S')

        if not state:
            return f"🧠 <b>INTELLIGENCE</b>\n━━━━━━━━━━━━━\n⏳ No data available.", self.get_intelligence_keyboard()

        price = state.get('price', 0)
        regime = state.get('regime', 'unknown')
        strategy = state.get('strategy', 'unknown')
        rsi = state.get('rsi', 50)
        volatility = state.get('volatility', 'N/A')
        trend = state.get('trend', 'N/A')
        samples = state.get('learning_samples', 0)
        min_samples = state.get('learning_min_samples', 50)
        retrains = state.get('learning_retrains', 0)
        is_trained = state.get('learning_trained', False)
        signal_action = state.get('signal_action', 'hold')
        signal_conf = state.get('signal_confidence', 0)
        signal_ma = state.get('signal_ma', 'neutral')
        daily_signals = state.get('daily_signals', 0)

        model_status = '✅ Trained' if is_trained else '⏳ Learning'
        sample_pct = (samples / min_samples * 100) if min_samples > 0 else 0

        # RSI signal
        if rsi < 30:
            rsi_sig = 'oversold (BUY)'
        elif rsi > 70:
            rsi_sig = 'overbought (SELL)'
        else:
            rsi_sig = 'neutral'

        # Regime description
        regime_desc = {
            'bull': 'bullish trend detected',
            'bear': 'bearish trend detected',
            'volatile': 'high volatility',
            'sideways': 'stable market'
        }.get(regime, 'unknown')

        msg = (
            f"🧠 <b>AI INTELLIGENCE</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🕐 {ts}\n\n"
            f"📊 <b>MARKET DATA</b>\n"
            f"├─ Price: {_fmt_dollars(price)}\n"
            f"├─ Regime: {_regime_emoji(regime)} {regime.upper()}\n"
            f"├─ Regime Detail: {regime_desc}\n"
            f"├─ Trend: {trend}\n"
            f"├─ RSI: {rsi:.1f} ({rsi_sig})\n"
            f"└─ Volatility: {volatility}\n\n"
            f"🧠 <b>AI MODEL</b>\n"
            f"├─ Strategy: {strategy}\n"
            f"├─ Model: {model_status}\n"
            f"├─ Samples: {samples}/{min_samples} ({sample_pct:.0f}%)\n"
            f"├─ Retrains: {retrains}\n"
            f"├─ MA Signal: {signal_ma}\n"
            f"└─ Confidence: {signal_conf:.0%}\n\n"
            f"⚡ <b>SIGNAL</b>\n"
            f"├─ Action: {_action_emoji(signal_action)} {signal_action.upper()}\n"
            f"└─ Signals Evaluated: {daily_signals}"
        )
        return msg, self.get_intelligence_keyboard()

    def format_risk_view(self) -> Tuple[str, List[List[Dict]]]:
        state = load_dashboard_state()
        ts = datetime.now().strftime('%H:%M:%S')

        if not state:
            return f"🛡️ <b>RISK STATUS</b>\n━━━━━━━━━━━━━\n⏳ No data available.", self.get_risk_keyboard()

        daily_trades = state.get('daily_trades', 0)
        max_trades = state.get('daily_max_trades', 5)
        stop_loss = state.get('stop_loss_pct', 0.02) * 100
        take_profit = state.get('take_profit_pct', 0.05) * 100
        circuit_ok = state.get('circuit_breaker_ok', True)
        balance = state.get('balance', 0)
        position_amt = state.get('position_amount', 0)
        price = state.get('price', 0)
        pnl_pct = state.get('position_pnl_pct', 0)
        daily_wins = state.get('daily_wins', 0)
        daily_losses = state.get('daily_losses', 0)

        # Determine risk level
        if daily_trades >= max_trades:
            risk_level = '🔴 HIGH (limit reached)'
        elif pnl_pct < -1.5 or not circuit_ok:
            risk_level = '🟡 MEDIUM'
        else:
            risk_level = '🟢 LOW'

        exposed_usd = position_amt * price
        exposed_pct = (exposed_usd / balance * 100) if balance > 0 else 0

        circuit_label = '✅ CLOSED' if circuit_ok else '❌ OPEN'
        trade_limit_status = '🔴 STOPPED' if daily_trades >= max_trades else '🟢 ACTIVE'

        msg = (
            f"🛡️ <b>RISK STATUS</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🕐 {ts}\n\n"
            f"📋 <b>DAILY LIMITS</b>\n"
            f"├─ Trades: {daily_trades}/{max_trades}\n"
            f"├─ Status: {trade_limit_status}\n"
            f"├─ Wins: {daily_wins}  |  Losses: {daily_losses}\n"
            f"└─ Daily PnL: {_fmt_pct(pnl_pct if daily_trades > 0 else 0)}\n\n"
            f"⚙️ <b>PROTECTION</b>\n"
            f"├─ Stop Loss: -{stop_loss:.1f}%\n"
            f"├─ Take Profit: +{take_profit:.1f}%\n"
            f"├─ Circuit Breaker: {circuit_label}\n"
            f"└─ Risk Level: {risk_level}\n\n"
            f"📊 <b>EXPOSURE</b>\n"
            f"├─ Position: {_fmt_dollars(exposed_usd)} ({exposed_pct:.2f}% of balance)\n"
            f"├─ Leverage: {state.get('leverage', 75)}x\n"
            f"└─ Current PnL: {_fmt_pct(pnl_pct)}"
        )
        return msg, self.get_risk_keyboard()

    def format_welcome(self) -> Tuple[str, List[List[Dict]]]:
        ts = datetime.now().strftime('%H:%M:%S')
        version = self.config.get('watchtower', {}).get('version', '1.0.0')
        msg = (
            f"🤖 <b>NKHEKHE ALPHA — Trading Dashboard</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ System Status: Online\n"
            f"📅 Version: {version}\n"
            f"🔐 Access: Admin Authorized\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Use the dashboard buttons below or type /help for commands."
        )
        return msg, self.get_main_menu_keyboard()

    # ═══════════════════════════════════════════════════════════════════════════
    # CALLBACK HANDLER
    # ═══════════════════════════════════════════════════════════════════════════

    def handle_callback(self, callback_data: str, chat_id: int, bot) -> Optional[str]:
        action = callback_data
        try:
            # ── Dashboard sections ──
            if action in ('main', CALLBACK_ACTIONS['main_menu']):
                msg, kb = self.format_main_menu()
                bot.edit_message_reply_markup(chat_id, msg, reply_markup=kb)
                return None

            elif action in (CALLBACK_ACTIONS['portfolio'], CALLBACK_ACTIONS['refresh_portfolio'], CALLBACK_ACTIONS['nav_portfolio']):
                msg, kb = self.format_portfolio_view()
                bot.edit_message_reply_markup(chat_id, msg, reply_markup=kb)
                return None

            elif action in (CALLBACK_ACTIONS['intelligence'], CALLBACK_ACTIONS['refresh_intel'], CALLBACK_ACTIONS['nav_intel']):
                msg, kb = self.format_intelligence_view()
                bot.edit_message_reply_markup(chat_id, msg, reply_markup=kb)
                return None

            elif action in (CALLBACK_ACTIONS['risk'], CALLBACK_ACTIONS['refresh_risk'], CALLBACK_ACTIONS['nav_risk']):
                msg, kb = self.format_risk_view()
                bot.edit_message_reply_markup(chat_id, msg, reply_markup=kb)
                return None

            # ── Trading sub-menu ──
            elif action == CALLBACK_ACTIONS['trading_menu']:
                msg = "📈 <b>TRADING CONTROL</b>\n\nSelect an action:"
                bot.edit_message_reply_markup(chat_id, msg, reply_markup=self.get_trading_menu_keyboard())
                return None

            elif action == CALLBACK_ACTIONS['nav_trading']:
                msg = "📈 <b>TRADING CONTROL</b>\n\nSelect an action:"
                bot.edit_message_reply_markup(chat_id, msg, reply_markup=self.get_trading_menu_keyboard())
                return None

            # ── System sub-menu ──
            elif action in (CALLBACK_ACTIONS['system_menu'], CALLBACK_ACTIONS['nav_system']):
                msg = "⚙️ <b>SYSTEM CONTROL</b>\n\nSelect an option:"
                bot.edit_message_reply_markup(chat_id, msg, reply_markup=self.get_system_menu_keyboard())
                return None

            # ── Trading actions ──
            elif action == 'trade_long':
                if bot.command_processor.trading_engine:
                    return bot.command_processor.cmd_long(chat_id, '/long 0.001', bot)
                return "❌ Trading engine not initialized"

            elif action == 'trade_short':
                if bot.command_processor.trading_engine:
                    return bot.command_processor.cmd_short(chat_id, '/short 0.001', bot)
                return "❌ Trading engine not initialized"

            elif action == 'trade_close':
                if bot.command_processor.trading_engine:
                    return bot.command_processor.cmd_close(chat_id, '/close', bot)
                return "❌ Trading engine not initialized"

            elif action == 'trade_balance':
                if bot.command_processor.trading_engine:
                    return bot.command_processor.cmd_balance(chat_id, '/balance', bot)
                return "❌ Trading engine not initialized"

            elif action == 'trade_leverage':
                if bot.command_processor.trading_engine:
                    return bot.command_processor.cmd_leverage(chat_id, '/leverage', bot)
                return "❌ Trading engine not initialized"

            elif action == 'trade_positions':
                if bot.command_processor.trading_engine:
                    return bot.command_processor.cmd_positions(chat_id, '/positions', bot)
                return "❌ Trading engine not initialized"

            elif action == 'trade_signal':
                if bot.command_processor.trading_engine:
                    return bot.command_processor.cmd_signal(chat_id, '/signal', bot)
                return "❌ Trading engine not initialized"

            elif action == 'trade_history':
                if bot.command_processor.trading_engine:
                    return bot.command_processor.cmd_history(chat_id, '/history', bot)
                return "❌ Trading engine not initialized"

            elif action == 'trade_status':
                if bot.command_processor.trading_engine:
                    return bot.command_processor.cmd_trade_status(chat_id, '/trade', bot)
                return "❌ Trading engine not initialized"

            elif action == 'trade_start':
                if bot.command_processor.trading_engine:
                    bot.command_processor.trading_engine.start()
                    return "🟢 Trading engine started"
                return "❌ Trading engine not initialized"

            elif action == 'trade_stop':
                if bot.command_processor.trading_engine:
                    bot.command_processor.trading_engine.stop()
                    return "🔴 Trading engine stopped"
                return "❌ Trading engine not initialized"

            # ── System control ──
            elif action == CALLBACK_ACTIONS['system_on']:
                return self._system_on(bot)

            elif action == CALLBACK_ACTIONS['system_off']:
                return self._system_off(bot)

            elif action == CALLBACK_ACTIONS['restart']:
                return self._system_restart(bot)

            # ── System info ──
            elif action == CALLBACK_ACTIONS['quick_status']:
                return bot.command_processor.cmd_quick_status(chat_id, '/sys', bot)

            elif action == CALLBACK_ACTIONS['detailed_status']:
                return bot.command_processor.cmd_status(chat_id, '/status', bot)

            elif action == CALLBACK_ACTIONS['metrics']:
                return bot.command_processor.cmd_metrics(chat_id, '/metrics', bot)

            elif action == CALLBACK_ACTIONS['workflows']:
                return bot.command_processor.cmd_workflows(chat_id, '/workflows', bot)

            elif action == CALLBACK_ACTIONS['agents']:
                return bot.command_processor.cmd_agents(chat_id, '/agents', bot)

            elif action == CALLBACK_ACTIONS['logs']:
                return bot.command_processor.cmd_logs(chat_id, '/logs', bot)

            elif action == CALLBACK_ACTIONS['alerts']:
                return bot.command_processor.cmd_alerts(chat_id, '/alerts', bot)

            # ── Hide ──
            elif action == CALLBACK_ACTIONS['hide_menu']:
                return "🔒 Menu hidden. Send /menu to show it again."

            else:
                logger.warning(f"Unknown callback: {action}")
                return None

        except Exception as e:
            logger.error(f"Callback handler error: {e}")
            return f"❌ Error: {str(e)}"

    # ═══════════════════════════════════════════════════════════════════════════
    # SYSTEM CONTROL HELPERS
    # ═══════════════════════════════════════════════════════════════════════════

    def _system_on(self, bot) -> str:
        logger.info("System start requested via menu")
        script_path = '/home/ubuntu/financial_orchestrator/start_systemd.sh'
        if not os.path.exists(script_path):
            return "❌ Start script not found"
        try:
            result = subprocess.run(['/bin/bash', script_path], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return "✅ <b>Starting System</b>\n\nAll components are being started..."
            return f"❌ Start failed:\n<code>{result.stderr[:200]}</code>"
        except subprocess.TimeoutExpired:
            return "❌ Start command timed out"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def _system_off(self, bot) -> str:
        logger.info("System stop requested via menu")
        script_path = '/home/ubuntu/financial_orchestrator/stop_systemd.sh'
        if not os.path.exists(script_path):
            return "❌ Stop script not found"
        try:
            result = subprocess.run(['/bin/bash', script_path], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return "🔴 <b>Stopping System</b>\n\nAll components are being stopped..."
            return f"❌ Stop failed:\n<code>{result.stderr[:200]}</code>"
        except subprocess.TimeoutExpired:
            return "❌ Stop command timed out"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def _system_restart(self, bot) -> str:
        logger.info("System restart requested via menu")
        try:
            stop_script = '/home/ubuntu/financial_orchestrator/stop_systemd.sh'
            start_script = '/home/ubuntu/financial_orchestrator/start_systemd.sh'
            subprocess.run(['/bin/bash', stop_script], capture_output=True, timeout=15)
            subprocess.run(['/bin/bash', start_script], capture_output=True, timeout=30)
            return "🔄 <b>Restarting System</b>\n\nSystem is being restarted..."
        except Exception as e:
            return f"❌ Restart error: {str(e)}"
