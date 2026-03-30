#!/usr/bin/env python3
"""
Command Processor for Telegram Watch Tower
Handles user commands and generates responses (HTML formatted)
"""

import logging
import json
import os
import sys
import subprocess
from datetime import datetime
from typing import Dict, Optional

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger('CommandProcessor')

# Import shared state reader from bot_menu (no duplicate)
from telegram_watchtower.bot_menu import load_dashboard_state

# Commands that are actions (should NOT get dashboard keyboard appended)
ACTION_COMMANDS = {'/long', '/short', '/close', '/systemon', '/systemoff', '/hide'}


class CommandProcessor:
    def __init__(self, config: Dict):
        self.config = config
        self.commands = config.get('watchtower', {}).get('commands', [])
        
        self.command_handlers = {
            '/start': self.cmd_start,
            '/hello': self.cmd_start,
            '/menu': self.cmd_menu,
            '/hide': self.cmd_hide,
            '/status': self.cmd_status,
            '/s': self.cmd_status,
            '/workflows': self.cmd_workflows,
            '/wf': self.cmd_workflows,
            '/agents': self.cmd_agents,
            '/ag': self.cmd_agents,
            '/logs': self.cmd_logs,
            '/log': self.cmd_logs,
            '/metrics': self.cmd_metrics,
            '/m': self.cmd_metrics,
            '/alerts': self.cmd_alerts,
            '/a': self.cmd_alerts,
            '/data': self.cmd_data,
            '/d': self.cmd_data,
            '/systemon': self.cmd_system_on,
            '/systemoff': self.cmd_system_off,
            '/sys': self.cmd_quick_status,
            '/help': self.cmd_help,
            '/h': self.cmd_help,
            '/?': self.cmd_help,
            
            '/long': self.cmd_long,
            '/short': self.cmd_short,
            '/close': self.cmd_close,
            '/balance': self.cmd_balance,
            '/positions': self.cmd_positions,
            '/leverage': self.cmd_leverage,
            '/signal': self.cmd_signal,
            '/history': self.cmd_history,
            '/trade': self.cmd_trade_status,
            '/futures': self.cmd_trade_status,
            
            # Dashboard commands
            '/dashboard': self.cmd_dashboard,
            '/dash': self.cmd_dashboard,
            '/intel': self.cmd_intel,
            '/portfolio': self.cmd_portfolio,
            '/market': self.cmd_market,
            '/risk': self.cmd_risk,
        }
        
        self.trading_engine = None
    
    def set_trading_engine(self, engine):
        """Set the trading engine for futures commands."""
        self.trading_engine = engine
    
    def process(self, chat_id: int, text: str, bot) -> str:
        """Process a command and return response"""
        command = text.strip().split()[0] if text.strip() else ''
        
        if not command:
            return "Please send a command. Type /help for available commands."
        
        if command in self.command_handlers:
            try:
                return self.command_handlers[command](chat_id, text, bot)
            except Exception as e:
                logger.error(f"Command processing error: {e}")
                return f"Error processing command: {str(e)}"
        else:
            return f"Unknown command: {command}\nType /help for available commands."
    
    def get_main_menu_keyboard(self):
        """Get the unified dashboard main menu keyboard"""
        return [
            [
                {"text": "🤖 Portfolio", "callback_data": "dash_portfolio"},
                {"text": "🧠 Intelligence", "callback_data": "dash_intel"},
                {"text": "🛡️ Risk", "callback_data": "dash_risk"},
            ],
            [
                {"text": "📈 Trading", "callback_data": "trading_menu"},
                {"text": "⚙️ System", "callback_data": "system_menu"},
                {"text": "🔔 Alerts", "callback_data": "info_alerts"},
            ],
            [
                {"text": "🟢 System On", "callback_data": "sys_on"},
                {"text": "🔴 System Off", "callback_data": "sys_off"},
                {"text": "🔄 Restart", "callback_data": "sys_restart"},
            ],
            [
                {"text": "🔒 Hide Menu", "callback_data": "hide"},
            ],
        ]
    
    # ═══════════════════════════════════════════════════════════════
    # CORE COMMANDS
    # ═══════════════════════════════════════════════════════════════
    
    def cmd_start(self, chat_id: int, text: str, bot) -> str:
        """Handle /start command - Show welcome with dashboard state"""
        state = load_dashboard_state()
        ts = datetime.now().strftime('%H:%M:%S')
        version = self.config.get('watchtower', {}).get('version', '1.0.0')
        
        header = (
            f"🤖 <b>NKHEKHE ALPHA — Trading Dashboard</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🕐 {ts}  |  v{version}\n"
            f"✅ System: Online  |  🔐 Admin: Authorized\n"
        )
        
        if state:
            price = state.get('price', 0)
            regime = state.get('regime', 'unknown')
            position_side = state.get('position_side', 'FLAT')
            pnl_pct = state.get('position_pnl_pct', 0)
            balance = state.get('balance', 0)
            daily_trades = state.get('daily_trades', 0)
            max_trades = state.get('daily_max_trades', 5)
            signal_action = state.get('signal_action', 'hold')
            signal_conf = state.get('signal_confidence', 0)
            uptime = self._format_uptime(state.get('uptime', 0))
            
            regime_emoji = {'bull': '🐂', 'bear': '🐻', 'volatile': '⚡', 'sideways': '➡️'}.get(regime, '❓')
            action_emoji = {'buy': '🟢', 'sell': '🔴', 'hold': '⏸️'}.get(signal_action, '❓')
            side_emoji = '📈' if position_side == 'LONG' else '📉' if position_side == 'SHORT' else '➡️'
            pnl_emoji = '🟢' if pnl_pct > 0 else '🔴' if pnl_pct < 0 else '⚪'
            
            body = (
                f"\n📊 <b>MARKET</b>\n"
                f"├─ Price: ${price:,.2f}\n"
                f"├─ Regime: {regime_emoji} {regime.upper()}\n"
                f"└─ Signal: {action_emoji} {signal_action.upper()} ({signal_conf:.0%})\n"
                f"\n💼 <b>POSITION</b>\n"
                f"├─ {side_emoji} {position_side}\n"
                f"└─ PnL: {pnl_emoji} {pnl_pct:+.2f}%\n"
                f"\n💰 <b>ACCOUNT</b>\n"
                f"├─ Balance: ${balance:,.2f}\n"
                f"├─ Trades: {daily_trades}/{max_trades}\n"
                f"└─ Uptime: {uptime}\n"
            )
        else:
            body = (
                f"\n⏳ <i>Waiting for trading data...\n"
                f"Start autonomous_trading.py to see live dashboard.</i>\n"
            )
        
        footer = (
            f"\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Use buttons below or /help for commands</i>"
        )
        
        return header + body + footer
    
    def cmd_menu(self, chat_id: int, text: str, bot) -> str:
        """Handle /menu command - Show main menu"""
        return (
            "🤖 <b>NKHEKHE ALPHA DASHBOARD</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Select a section below to view trading data."
        )
    
    def cmd_hide(self, chat_id: int, text: str, bot) -> str:
        """Handle /hide command - Hide menu"""
        return "🔒 Menu hidden. Send /menu to show it again."
    
    # ═══════════════════════════════════════════════════════════════
    # SYSTEM COMMANDS (HTML)
    # ═══════════════════════════════════════════════════════════════
    
    def cmd_status(self, chat_id: int, text: str, bot) -> str:
        """Get system status"""
        status = bot.get_status()
        metrics = bot.get_system_metrics()
        
        uptime_str = self._format_uptime(status.get('uptime_seconds', 0))
        
        return (
            f"📋 <b>SYSTEM STATUS</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"ℹ️ <b>Name:</b> {status['name']}\n"
            f"⭐ <b>Version:</b> {status['version']}\n"
            f"✅ <b>Status:</b> {status['status']}\n"
            f"⏱ <b>Uptime:</b> {uptime_str}\n"
            f"🔔 <b>Alerts:</b> {status.get('alerts_count', 0)}\n\n"
            f"💾 <b>Memory</b>\n"
            f"├─ Total: {metrics['memory'].get('total_mb', 0):.0f} MB\n"
            f"├─ Used: {metrics['memory'].get('used_mb', 0):.0f} MB\n"
            f"├─ Available: {metrics['memory'].get('available_mb', 0):.0f} MB\n"
            f"└─ Usage: {metrics['memory'].get('usage_percent', 0):.1f}%"
        )
    
    def cmd_workflows(self, chat_id: int, text: str, bot) -> str:
        """Get active workflows"""
        workflow_file = '/home/ubuntu/financial_orchestrator/logs/e2e_workflow_state.json'
        
        response = "📁 <b>ACTIVE WORKFLOWS</b>\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        if os.path.exists(workflow_file):
            try:
                with open(workflow_file, 'r') as f:
                    workflow = json.load(f)
                
                response += (
                    f"\n⭐ <b>Workflow ID:</b> {workflow.get('workflow_id', 'N/A')}\n"
                    f"✅ <b>Status:</b> {workflow.get('status', 'unknown')}\n"
                    f"💻 <b>Progress:</b> {workflow.get('progress_percentage', 0)}%\n"
                    f"🕐 <b>Phases:</b> {len(workflow.get('phases', []))}\n"
                )
                
                if workflow.get('phases'):
                    response += "\n<b>Phases:</b>\n"
                    for phase in workflow['phases']:
                        icon = "✅" if phase.get('status') == 'completed' else "⏳"
                        response += f"  {icon} {phase.get('name', 'Unknown')}\n"
            except Exception as e:
                response += f"\n❌ Error loading workflow: {e}"
        else:
            response += f"\n📄 No workflow state file found"
        
        return response.rstrip()
    
    def cmd_agents(self, chat_id: int, text: str, bot) -> str:
        """Get agent statuses"""
        try:
            from optimization.agent_optimizer import AgentOptimizer
            optimizer = AgentOptimizer()
            status = optimizer.get_optimization_status()
            
            response = (
                f"💻 <b>AGENT STATUS</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"✅ <b>Optimization Active:</b> {status['optimization_active']}\n"
                f"🤖 <b>Agents Tracked:</b> {status['agents_tracked']}\n"
                f"📋 <b>Workflows Tracked:</b> {status['workflows_tracked']}\n"
            )
            
            if status['agents_tracked'] > 0:
                response += "\n<b>Agent Details:</b>\n"
                for agent_id, data in optimizer.agent_performance.items():
                    response += f"  • {agent_id}: {data['tasks_completed']} tasks\n"
            
            return response.rstrip()
            
        except Exception as e:
            return f"💻 <b>AGENT STATUS</b>\n━━━━━━━━━━━━━━━━━━━━━━━━\n❌ Error: {e}"
    
    def cmd_logs(self, chat_id: int, text: str, bot) -> str:
        """Get recent logs"""
        parts = text.strip().split()
        source_filter = None
        if len(parts) > 1:
            source_filter = parts[1]
        
        logs = ["📄 <b>RECENT LOGS</b>\n━━━━━━━━━━━━━━━━━━━━━━━━\n"]
        log_dir = '/home/ubuntu/financial_orchestrator/logs'
        
        if os.path.exists(log_dir):
            for log_file in ['risk_monitor.log', 'workflow_nohup.log', 'optimizer_nohup.log']:
                if source_filter and source_filter.lower() not in log_file.lower():
                    continue
                
                log_path = os.path.join(log_dir, log_file)
                if os.path.exists(log_path):
                    try:
                        with open(log_path, 'r') as f:
                            lines = f.readlines()
                            recent = [l.strip() for l in lines[-5:] if l.strip()]
                            if recent:
                                logs.append(f"<b>{log_file}:</b>")
                                for line in recent:
                                    escaped = line.replace('<', '&lt;').replace('>', '&gt;')
                                    logs.append(f"  <code>{escaped[:100]}</code>")
                    except Exception as e:
                        logs.append(f"<b>{log_file}:</b> Error: {e}")
        
        if len(logs) == 1:
            return "📄 <b>RECENT LOGS</b>\n━━━━━━━━━━━━━━━━━━━━━━━━\n📁 No logs found"
        
        return "\n".join(logs[:20])
    
    def cmd_metrics(self, chat_id: int, text: str, bot) -> str:
        """Get system metrics"""
        metrics = bot.get_system_metrics()
        
        return (
            f"📈 <b>SYSTEM METRICS</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⏱ <b>Uptime:</b> {metrics.get('uptime', 'unknown')}\n\n"
            f"💾 <b>Memory</b>\n"
            f"├─ Total: {metrics['memory'].get('total_mb', 0):.0f} MB\n"
            f"├─ Used: {metrics['memory'].get('used_mb', 0):.0f} MB\n"
            f"├─ Available: {metrics['memory'].get('available_mb', 0):.0f} MB\n"
            f"└─ Usage: {metrics['memory'].get('usage_percent', 0):.1f}%"
        )
    
    def cmd_alerts(self, chat_id: int, text: str, bot) -> str:
        """Get recent alerts"""
        if bot.event_monitor:
            summary = bot.event_monitor.get_event_summary()
            
            response = (
                f"🔔 <b>RECENT ALERTS</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🔴 <b>Total Events:</b> {summary['total_events']}\n"
            )
            
            for event_type, count in summary['alert_counts'].items():
                if count > 0:
                    response += f"  • {event_type}: {count}\n"
            
            if summary['recent_events']:
                response += "\n<b>Latest Events:</b>\n"
                for event in summary['recent_events'][-3:]:
                    emoji = self._get_severity_emoji(event.get('severity', 'info'))
                    msg = event.get('message', '')[:50]
                    response += f"  {emoji} {event['type']}: {msg}...\n"
            
            return response.rstrip()
        else:
            return "🔔 <b>RECENT ALERTS</b>\n━━━━━━━━━━━━━━━━━━━━━━━━\n🔔 No event monitor available"
    
    def cmd_data(self, chat_id: int, text: str, bot) -> str:
        """Get data ingestion summary"""
        response = "📊 <b>DATA LAB STATUS</b>\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        try:
            from data_lab import get_stream_manager
            from data_lab.storage import get_duckdb_manager
            
            stream_manager = get_stream_manager()
            stream_info = stream_manager.get_all_stream_info()
            
            response += "\n<b>Redis Streams:</b>\n"
            for stream_name, info in stream_info.items():
                utilization = info.get('utilization_percent', 0)
                emoji = "🟢" if utilization < 80 else "🟡" if utilization < 95 else "🔴"
                response += (
                    f"  {emoji} {stream_name}: {info.get('length', 0)}/{info.get('max_length', 0)} "
                    f"({utilization:.1f}%)\n"
                )
            
            db = get_duckdb_manager()
            db_stats = db.get_stats()
            
            response += (
                f"\n<b>DuckDB Storage:</b>\n"
                f"  📊 Ticks: {db_stats.get('tick_count', 0):,}\n"
                f"  📊 Klines: {db_stats.get('kline_count', 0):,}\n"
                f"  💾 Size: {db_stats.get('file_size_mb', 0):.1f} MB\n"
            )
            
            symbols = db_stats.get('tracked_symbols', [])
            if symbols:
                response += f"  📈 Symbols: {', '.join(symbols[:5])}\n"
                if len(symbols) > 5:
                    response += f"     +{len(symbols) - 5} more\n"
                    
        except Exception as e:
            response += f"\n⚠️ Error loading data stats: {e}"
        
        return response.rstrip()
    
    # ═══════════════════════════════════════════════════════════════
    # SYSTEM CONTROL COMMANDS
    # ═══════════════════════════════════════════════════════════════
    
    def cmd_system_on(self, chat_id: int, text: str, bot) -> str:
        """Start the entire system"""
        logger.info(f"System start requested by chat_id={chat_id}")
        
        script_path = '/home/ubuntu/financial_orchestrator/start_systemd.sh'
        
        if not os.path.exists(script_path):
            return "❌ Start script not found"
        
        try:
            result = subprocess.run(
                ['/bin/bash', script_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return "✅ <b>SYSTEM STARTING</b>\n\nAll components are being started."
            else:
                logger.error(f"Start script failed: {result.stderr}")
                return f"❌ <b>Start failed:</b>\n<code>{result.stderr[:200]}</code>"
        except subprocess.TimeoutExpired:
            return "❌ Start command timed out"
        except Exception as e:
            logger.error(f"Start command error: {e}")
            return f"❌ Error: {str(e)}"
    
    def cmd_system_off(self, chat_id: int, text: str, bot) -> str:
        """Stop the entire system"""
        logger.info(f"System stop requested by chat_id={chat_id}")
        
        script_path = '/home/ubuntu/financial_orchestrator/stop_systemd.sh'
        
        if not os.path.exists(script_path):
            return "❌ Stop script not found"
        
        try:
            result = subprocess.run(
                ['/bin/bash', script_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return "🛑 <b>SYSTEM STOPPING</b>\n\nAll components are being stopped."
            else:
                logger.error(f"Stop script failed: {result.stderr}")
                return f"❌ <b>Stop failed:</b>\n<code>{result.stderr[:200]}</code>"
        except subprocess.TimeoutExpired:
            return "❌ Stop command timed out"
        except Exception as e:
            logger.error(f"Stop command error: {e}")
            return f"❌ Error: {str(e)}"
    
    def cmd_quick_status(self, chat_id: int, text: str, bot) -> str:
        """Quick status check of all components"""
        logs_dir = '/home/ubuntu/financial_orchestrator/logs'
        
        components = [
            ('telegram', 'Telegram Bot'),
            ('risk', 'Risk Monitor'),
            ('validation', 'Validation Engine'),
            ('optimizer', 'Agent Optimizer'),
            ('workflow', 'Workflow Processor')
        ]
        
        response = "📊 <b>QUICK STATUS</b>\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        all_running = True
        
        for key, name in components:
            pid_file = os.path.join(logs_dir, f'{key}.pid')
            if os.path.exists(pid_file):
                try:
                    pid = int(open(pid_file).read().strip())
                    if psutil and psutil.pid_exists(pid):
                        response += f"✅ {name}\n"
                    else:
                        if os.path.exists(f'/proc/{pid}'):
                            response += f"✅ {name}\n"
                        else:
                            response += f"❌ {name} (stale PID)\n"
                            all_running = False
                except:
                    response += f"❌ {name} (error)\n"
                    all_running = False
            else:
                response += f"❌ {name} (not running)\n"
                all_running = False
        
        response += f"\n{'🟢 All systems operational' if all_running else '⚠️ Some systems down'}"
        
        return response
    
    # ═══════════════════════════════════════════════════════════════
    # TRADING COMMANDS
    # ═══════════════════════════════════════════════════════════════
    
    def cmd_long(self, chat_id: int, text: str, bot) -> str:
        """Open LONG position"""
        if not self.trading_engine:
            return "❌ Trading engine not initialized. Use /trade to start."
        
        parts = text.strip().split()
        quantity = 0.001
        
        if len(parts) > 1:
            try:
                quantity = float(parts[1])
            except ValueError:
                return "❌ Invalid quantity. Usage: /long 0.001"
        
        result = self.trading_engine.long(quantity)
        
        if 'orderId' in result:
            order = result.get('order', {})
            return (
                f"📈 <b>LONG OPENED</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"✅ <b>Order ID:</b> {order.get('orderId')}\n"
                f"💰 <b>Symbol:</b> {order.get('symbol')}\n"
                f"📊 <b>Quantity:</b> {order.get('executedQty')}\n"
                f"💵 <b>Price:</b> ${float(order.get('avgPrice', 0)):,.2f}\n"
                f"⚡ <b>Leverage:</b> {result.get('leverage', 75)}x"
            )
        elif 'error' in result:
            return f"❌ Error: {result['error']}"
        
        return "❌ Order failed"
    
    def cmd_short(self, chat_id: int, text: str, bot) -> str:
        """Open SHORT position"""
        if not self.trading_engine:
            return "❌ Trading engine not initialized. Use /trade to start."
        
        parts = text.strip().split()
        quantity = 0.001
        
        if len(parts) > 1:
            try:
                quantity = float(parts[1])
            except ValueError:
                return "❌ Invalid quantity. Usage: /short 0.001"
        
        result = self.trading_engine.short(quantity)
        
        if 'orderId' in result:
            order = result.get('order', {})
            return (
                f"📉 <b>SHORT OPENED</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"✅ <b>Order ID:</b> {order.get('orderId')}\n"
                f"💰 <b>Symbol:</b> {order.get('symbol')}\n"
                f"📊 <b>Quantity:</b> {order.get('executedQty')}\n"
                f"💵 <b>Price:</b> ${float(order.get('avgPrice', 0)):,.2f}\n"
                f"⚡ <b>Leverage:</b> {result.get('leverage', 75)}x"
            )
        elif 'error' in result:
            return f"❌ Error: {result['error']}"
        
        return "❌ Order failed"
    
    def cmd_close(self, chat_id: int, text: str, bot) -> str:
        """Close position"""
        if not self.trading_engine:
            return "❌ Trading engine not initialized. Use /trade to start."
        
        result = self.trading_engine.close()
        
        if 'orderId' in result or result.get('message') == 'No position':
            status = self.trading_engine.get_status()
            position = status.get('position', {})
            
            if position and position.get('amount', 0) != 0:
                return "❌ Failed to close position"
            
            return "🛑 <b>POSITION CLOSED</b>\n━━━━━━━━━━━━━━━━━━━━━━━━\n✅ All positions closed successfully"
        elif 'error' in result:
            return f"❌ Error: {result['error']}"
        
        return "❌ Close failed"
    
    def cmd_balance(self, chat_id: int, text: str, bot) -> str:
        """Show balance"""
        if not self.trading_engine:
            return "❌ Trading engine not initialized. Use /trade to start."
        
        status = self.trading_engine.get_status()
        balance = status.get('balance', 0)
        wallet = status.get('wallet', {})
        
        return (
            f"💰 <b>WALLET BALANCE</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>USDT:</b> ${balance:,.2f}\n"
            f"<b>Unrealized PnL:</b> ${wallet.get('total_unrealized_pnl', 0):.2f}\n"
            f"<b>Total:</b> ${wallet.get('total_assets_value', balance):,.2f}\n"
            f"<b>Leverage:</b> {status.get('leverage', 75)}x\n"
            f"<b>Mode:</b> {'TESTNET' if status.get('testnet') else 'LIVE'} 🚨"
        )
    
    def cmd_positions(self, chat_id: int, text: str, bot) -> str:
        """Show open positions"""
        if not self.trading_engine:
            return "❌ Trading engine not initialized. Use /trade to start."
        
        status = self.trading_engine.get_status()
        position = status.get('position', {})
        
        if not position or position.get('amount', 0) == 0:
            return "📊 <b>OPEN POSITIONS</b>\n━━━━━━━━━━━━━━━━━━━━━━━━\n📊 No open positions"
        
        amount = position.get('amount', 0)
        side = "📈 LONG" if amount > 0 else "📉 SHORT"
        
        return (
            f"📊 <b>OPEN POSITION</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>Side:</b> {side}\n"
            f"<b>Amount:</b> {abs(amount)} BTC\n"
            f"<b>Entry:</b> ${position.get('entry_price', 0):,.2f}\n"
            f"<b>Leverage:</b> {position.get('leverage', 75)}x\n"
            f"<b>Unrealized PnL:</b> ${position.get('unrealized_pnl', 0):.2f}"
        )
    
    def cmd_leverage(self, chat_id: int, text: str, bot) -> str:
        """Set or show leverage"""
        if not self.trading_engine:
            return "❌ Trading engine not initialized. Use /trade to start."
        
        parts = text.strip().split()
        
        if len(parts) > 1:
            try:
                leverage = int(parts[1])
                if leverage < 1 or leverage > 75:
                    return "❌ Leverage must be between 1 and 75"
                
                self.trading_engine.set_leverage(leverage)
                return f"⚡ <b>LEVERAGE SET</b>\n\n✅ Leverage set to {leverage}x"
                
            except ValueError:
                return "❌ Invalid leverage. Usage: /leverage 25"
        
        status = self.trading_engine.get_status()
        return f"⚡ <b>CURRENT LEVERAGE:</b> {status.get('leverage', 75)}x"
    
    def cmd_signal(self, chat_id: int, text: str, bot) -> str:
        """Show current trading signal"""
        if not self.trading_engine:
            return "❌ Trading engine not initialized. Use /trade to start."
        
        status = self.trading_engine.get_status()
        price = status.get('price', 0)
        
        return (
            f"📈 <b>TRADING SIGNAL</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>Symbol:</b> {status.get('symbol', 'BTCUSDT')}\n"
            f"<b>Price:</b> ${price:,.2f}\n"
            f"<b>Leverage:</b> {status.get('leverage', 75)}x\n"
            f"<b>Mode:</b> {'TESTNET' if status.get('testnet') else 'LIVE'} 🚨"
        )
    
    def cmd_history(self, chat_id: int, text: str, bot) -> str:
        """Show trade history"""
        if not self.trading_engine:
            return "❌ Trading engine not initialized. Use /trade to start."
        
        history = self.trading_engine.get_trade_history(limit=5)
        
        if not history:
            return "📜 <b>TRADE HISTORY</b>\n━━━━━━━━━━━━━━━━━━━━━━━━\n📜 No trade history"
        
        response = "📜 <b>TRADE HISTORY</b>\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for trade in history[:5]:
            side = "📈" if trade.get('side') == 'BUY' else "📉"
            response += f"{side} {trade.get('symbol')} {trade.get('executedQty')} @ ${float(trade.get('price', 0)):,.0f}\n"
        
        return response.rstrip()
    
    def cmd_trade_status(self, chat_id: int, text: str, bot) -> str:
        """Start or show trading status"""
        if not self.trading_engine:
            return "❌ Trading engine not initialized."
        
        status = self.trading_engine.get_status()
        position = status.get('position', {})
        
        running = "🟢" if status.get('running') else "🔴"
        
        return (
            f"🚀 <b>TRADING ENGINE</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>Status:</b> {running} {'Running' if status.get('running') else 'Stopped'}\n"
            f"<b>Symbol:</b> {status.get('symbol', 'BTCUSDT')}\n"
            f"<b>Price:</b> ${status.get('price', 0):,.2f}\n"
            f"<b>Balance:</b> ${status.get('balance', 0):,.2f}\n"
            f"<b>Leverage:</b> {status.get('leverage', 75)}x\n"
            f"<b>Mode:</b> {'TESTNET' if status.get('testnet') else 'LIVE'} 🚨\n\n"
            f"<b>Position:</b> {position.get('amount', 0) if position else 0} BTC\n"
            f"<b>PnL:</b> ${position.get('unrealized_pnl', 0) if position else 0:.2f}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Commands: /long, /short, /close, /balance, /positions</i>"
        )

    # ═══════════════════════════════════════════════════════════════
    # DASHBOARD COMMANDS (HTML)
    # ═══════════════════════════════════════════════════════════════

    def cmd_dashboard(self, chat_id: int, text: str, bot) -> str:
        """Quick dashboard summary."""
        state = load_dashboard_state()
        if not state:
            return (
                "🤖 <b>DASHBOARD</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⏳ No data available.\n"
                "Start autonomous_trading.py to see live data."
            )

        price = state.get('price', 0)
        regime = state.get('regime', 'unknown')
        position_side = state.get('position_side', 'FLAT')
        pnl_pct = state.get('position_pnl_pct', 0)
        balance = state.get('balance', 0)
        daily_trades = state.get('daily_trades', 0)
        max_trades = state.get('daily_max_trades', 5)
        signal_action = state.get('signal_action', 'hold')
        signal_conf = state.get('signal_confidence', 0)
        uptime = self._format_uptime(state.get('uptime', 0))

        regime_emoji = {'bull': '🐂', 'bear': '🐻', 'volatile': '⚡', 'sideways': '➡️'}.get(regime, '❓')
        action_emoji = {'buy': '🟢', 'sell': '🔴', 'hold': '⏸️'}.get(signal_action, '❓')
        side_emoji = '📈' if position_side == 'LONG' else '📉' if position_side == 'SHORT' else '➡️'
        pnl_emoji = '🟢' if pnl_pct > 0 else '🔴' if pnl_pct < 0 else '⚪'

        return (
            f"🤖 <b>QUICK DASHBOARD</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏱ {uptime}  |  💰 ${balance:,.2f}\n\n"
            f"📊 Market: ${price:,.2f} | {regime_emoji} {regime.upper()}\n"
            f"📡 Signal: {action_emoji} {signal_action.upper()} ({signal_conf:.0%})\n"
            f"💼 Position: {side_emoji} {position_side} | PnL: {pnl_emoji} {pnl_pct:+.2f}%\n"
            f"📋 Trades: {daily_trades}/{max_trades}\n\n"
            f"<i>Use /intel /portfolio /market /risk for details</i>"
        )

    def cmd_intel(self, chat_id: int, text: str, bot) -> str:
        """AI Intelligence view."""
        state = load_dashboard_state()
        if not state:
            return "🧠 <b>INTELLIGENCE</b>\n━━━━━━━━━━━━━━━━━━━━━━━━\n⏳ No data available."

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

        regime_emoji = {'bull': '🐂', 'bear': '🐻', 'volatile': '⚡', 'sideways': '➡️'}.get(regime, '❓')
        action_emoji = {'buy': '🟢', 'sell': '🔴', 'hold': '⏸️'}.get(signal_action, '❓')
        model_status = '✅ Trained' if is_trained else '⏳ Learning'
        sample_pct = (samples / min_samples * 100) if min_samples > 0 else 0

        if rsi < 30:
            rsi_sig = 'oversold (BUY)'
        elif rsi > 70:
            rsi_sig = 'overbought (SELL)'
        else:
            rsi_sig = 'neutral'

        regime_desc = {
            'bull': 'bullish trend detected',
            'bear': 'bearish trend detected',
            'volatile': 'high volatility',
            'sideways': 'stable market'
        }.get(regime, 'unknown')

        return (
            f"🧠 <b>AI INTELLIGENCE</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 <b>MARKET</b>\n"
            f"├─ Price: ${price:,.2f}\n"
            f"├─ Regime: {regime_emoji} {regime.upper()} — {regime_desc}\n"
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
            f"├─ Action: {action_emoji} {signal_action.upper()}\n"
            f"└─ Signals Evaluated: {daily_signals}"
        )

    def cmd_portfolio(self, chat_id: int, text: str, bot) -> str:
        """Portfolio view."""
        state = load_dashboard_state()
        if not state:
            return "🤖 <b>PORTFOLIO</b>\n━━━━━━━━━━━━━━━━━━━━━━━━\n⏳ No data available."

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
        action_emoji = {'buy': '🟢', 'sell': '🔴', 'hold': '⏸️'}.get(signal_action, '❓')
        pos_size_usd = amount * price

        return (
            f"🤖 <b>PORTFOLIO DASHBOARD</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏱ {testnet_label}\n\n"
            f"📊 <b>POSITION</b>\n"
            f"├─ Side: {side_emoji} {position_side}\n"
            f"├─ Size: {amount:.4f} BTC (${pos_size_usd:,.2f})\n"
            f"├─ Entry: ${entry:,.2f}\n"
            f"├─ Current: ${price:,.2f}\n"
            f"└─ PnL: {pnl_emoji} ${pnl:.2f} ({pnl_pct:+.2f}%)\n\n"
            f"💰 <b>ACCOUNT</b>\n"
            f"├─ Balance: ${balance:,.2f}\n"
            f"├─ Leverage: {leverage}x\n"
            f"├─ Daily PnL: {pnl_pct:+.2f}%\n"
            f"├─ Win Rate: {win_rate:.1f}% ({daily_wins}W/{daily_losses}L)\n"
            f"└─ Trades: {daily_trades}/{max_trades}\n\n"
            f"📈 <b>SIGNAL</b>\n"
            f"├─ {action_emoji} {signal_action.upper()} ({signal_conf:.0%})"
        )

    def cmd_market(self, chat_id: int, text: str, bot) -> str:
        """Market data view."""
        state = load_dashboard_state()
        if not state:
            return "📊 <b>MARKET DATA</b>\n━━━━━━━━━━━━━━━━━━━━━━━━\n⏳ No data available."

        price = state.get('price', 0)
        regime = state.get('regime', 'unknown')
        rsi = state.get('rsi', 50)
        volatility = state.get('volatility', 'N/A')
        trend = state.get('trend', 'N/A')
        signal_action = state.get('signal_action', 'hold')
        signal_conf = state.get('signal_confidence', 0)
        signal_ma = state.get('signal_ma', 'neutral')

        regime_emoji = {'bull': '🐂', 'bear': '🐻', 'volatile': '⚡', 'sideways': '➡️'}.get(regime, '❓')
        action_emoji = {'buy': '🟢', 'sell': '🔴', 'hold': '⏸️'}.get(signal_action, '❓')

        if rsi < 30:
            rsi_sig = 'oversold (BUY)'
        elif rsi > 70:
            rsi_sig = 'overbought (SELL)'
        else:
            rsi_sig = 'neutral'

        return (
            f"📊 <b>MARKET DATA</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 <b>PRICE</b>\n"
            f"├─ Current: ${price:,.2f}\n"
            f"├─ Regime: {regime_emoji} {regime.upper()}\n"
            f"├─ Trend: {trend}\n"
            f"└─ Volatility: {volatility}\n\n"
            f"📈 <b>INDICATORS</b>\n"
            f"├─ RSI: {rsi:.1f} ({rsi_sig})\n"
            f"├─ MA Cross: {signal_ma}\n\n"
            f"📡 <b>SIGNAL</b>\n"
            f"├─ Action: {action_emoji} {signal_action.upper()}\n"
            f"└─ Confidence: {signal_conf:.0%}"
        )

    def cmd_risk(self, chat_id: int, text: str, bot) -> str:
        """Risk status view."""
        state = load_dashboard_state()
        if not state:
            return "🛡️ <b>RISK STATUS</b>\n━━━━━━━━━━━━━━━━━━━━━━━━\n⏳ No data available."

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
        leverage = state.get('leverage', 75)

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

        return (
            f"🛡️ <b>RISK STATUS</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📋 <b>DAILY LIMITS</b>\n"
            f"├─ Trades: {daily_trades}/{max_trades}\n"
            f"├─ Status: {trade_limit_status}\n"
            f"├─ Wins: {daily_wins}  |  Losses: {daily_losses}\n"
            f"└─ Daily PnL: {pnl_pct:+.2f}%\n\n"
            f"⚙️ <b>PROTECTION</b>\n"
            f"├─ Stop Loss: -{stop_loss:.1f}%\n"
            f"├─ Take Profit: +{take_profit:.1f}%\n"
            f"├─ Circuit Breaker: {circuit_label}\n"
            f"└─ Risk Level: {risk_level}\n\n"
            f"📊 <b>EXPOSURE</b>\n"
            f"├─ Position: ${exposed_usd:,.2f} ({exposed_pct:.2f}% of balance)\n"
            f"├─ Leverage: {leverage}x\n"
            f"└─ Current PnL: {pnl_pct:+.2f}%"
        )

    # ═══════════════════════════════════════════════════════════════
    # HELP COMMAND
    # ═══════════════════════════════════════════════════════════════

    def cmd_help(self, chat_id: int, text: str, bot) -> str:
        """Get help message"""
        return (
            "🤖 <b>NKHEKHE ALPHA — Bot Commands</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 <b>Dashboard</b>\n"
            "  <code>/dashboard</code> — Quick dashboard summary\n"
            "  <code>/intel</code> — AI intelligence &amp; regime\n"
            "  <code>/portfolio</code> — Portfolio &amp; position\n"
            "  <code>/market</code> — Market data &amp; indicators\n"
            "  <code>/risk</code> — Risk status &amp; protection\n\n"
            "🚀 <b>Futures Trading (75x)</b>\n"
            "  <code>/long [qty]</code> — Open LONG\n"
            "  <code>/short [qty]</code> — Open SHORT\n"
            "  <code>/close</code> — Close position\n"
            "  <code>/balance</code> — Wallet balance\n"
            "  <code>/positions</code> — Open positions\n"
            "  <code>/leverage [1-75]</code> — Set leverage\n"
            "  <code>/signal</code> — Trading signal\n"
            "  <code>/history</code> — Trade history\n"
            "  <code>/trade</code> — Trading status\n\n"
            "⚙️ <b>System Control</b>\n"
            "  <code>/systemon</code> — Start all components\n"
            "  <code>/systemoff</code> — Stop all components\n"
            "  <code>/sys</code> — Quick status check\n\n"
            "ℹ️ <b>System Info</b>\n"
            "  <code>/status</code> — Detailed status\n"
            "  <code>/workflows</code> — Active workflows\n"
            "  <code>/agents</code> — Agent statuses\n"
            "  <code>/logs</code> — Recent logs\n"
            "  <code>/metrics</code> — System metrics\n"
            "  <code>/alerts</code> — Recent alerts\n"
            "  <code>/help</code> — Show this help"
        )
    
    # ═══════════════════════════════════════════════════════════════
    # UTILITIES
    # ═══════════════════════════════════════════════════════════════

    def _format_uptime(self, seconds: float) -> str:
        """Format uptime seconds to human readable string"""
        if seconds is None:
            return "unknown"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def _get_severity_emoji(self, severity: str) -> str:
        """Get emoji for severity level"""
        return {
            'critical': '⚠️',
            'warning': '🟡',
            'error': '❌',
            'info': 'ℹ️'
        }.get(severity, 'ℹ️')
