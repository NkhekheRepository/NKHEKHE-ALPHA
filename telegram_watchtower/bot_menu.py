#!/usr/bin/env python3
"""
Bot Menu Module for Financial Orchestrator
Provides inline keyboard menus and callback handlers for Telegram bot
"""

import logging
import json
import os
import subprocess
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger('BotMenu')

CALLBACK_ACTIONS = {
    'main_menu': 'main',
    'system_on': 'sys_on',
    'system_off': 'sys_off',
    'restart': 'sys_restart',
    'quick_status': 'st_quick',
    'detailed_status': 'st_detailed',
    'metrics': 'st_metrics',
    'workflows': 'info_wf',
    'agents': 'info_ag',
    'logs': 'info_logs',
    'alerts': 'info_alerts',
    'hide_menu': 'hide',
}


class BotMenu:
    def __init__(self, config: Dict):
        self.config = config
    
    def get_main_menu_keyboard(self) -> List[List[Dict]]:
        """Get main menu keyboard layout"""
        return [
            [
                {"text": "🟢 System On", "callback_data": CALLBACK_ACTIONS['system_on']},
                {"text": "🔴 System Off", "callback_data": CALLBACK_ACTIONS['system_off']},
                {"text": "🔄 Restart", "callback_data": CALLBACK_ACTIONS['restart']},
            ],
            [
                {"text": "📊 Status", "callback_data": CALLBACK_ACTIONS['quick_status']},
                {"text": "📈 Metrics", "callback_data": CALLBACK_ACTIONS['metrics']},
                {"text": "🔔 Alerts", "callback_data": CALLBACK_ACTIONS['alerts']},
            ],
            [
                {"text": "📁 Workflows", "callback_data": CALLBACK_ACTIONS['workflows']},
                {"text": "💻 Agents", "callback_data": CALLBACK_ACTIONS['agents']},
                {"text": "📄 Logs", "callback_data": CALLBACK_ACTIONS['logs']},
            ],
            [
                {"text": "🔒 Hide Menu", "callback_data": CALLBACK_ACTIONS['hide_menu']},
            ],
        ]
    
    def format_main_menu(self) -> Tuple[str, List[List[Dict]]]:
        """Format main menu message and keyboard"""
        message = """✨ *Financial Orchestrator*
━━━━━━━━━━━━━━━━━━
Welcome! Use the buttons below to control and monitor your system.

*Control Panel*
Start, stop, or restart any component instantly.

*System Info*
View status, metrics, logs, and more.

*Quick Access*
All commands available with one tap."""

        return message, self.get_main_menu_keyboard()
    
    def format_welcome(self) -> Tuple[str, List[List[Dict]]]:
        """Format welcome message with main menu"""
        message = """🤖 *Financial Orchestrator Watch Tower*

━━━━━━━━━━━━━━━━━━

✅ *System Status:* Online
📅 *Version:* {version}
🔐 *Access:* Admin Authorized

━━━━━━━━━━━━━━━━━━

I will notify you of system events, alerts, and workflow updates in real-time.

Use the menu below or type commands directly."""

        return message, self.get_main_menu_keyboard()
    
    def handle_callback(self, callback_data: str, chat_id: int, bot) -> Optional[str]:
        """Handle callback query from inline keyboard"""
        action = callback_data
        
        try:
            if action == CALLBACK_ACTIONS['main_menu']:
                msg, keyboard = self.format_main_menu()
                bot.edit_message_reply_markup(chat_id, msg, reply_markup=keyboard)
                return None
            
            elif action == CALLBACK_ACTIONS['system_on']:
                return self._system_on(bot)
            
            elif action == CALLBACK_ACTIONS['system_off']:
                return self._system_off(bot)
            
            elif action == CALLBACK_ACTIONS['restart']:
                return self._system_restart(bot)
            
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
            
            elif action == CALLBACK_ACTIONS['hide_menu']:
                return "🔒 Menu hidden. Send /menu to show it again."
            
            else:
                logger.warning(f"Unknown callback action: {action}")
                return None
        
        except Exception as e:
            logger.error(f"Callback handler error: {e}")
            return f"❌ Error: {str(e)}"
    
    def _system_on(self, bot) -> str:
        """Start the system"""
        logger.info("System start requested via menu")
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
                return "✅ *Starting System*\n\nAll components are being started...\n\n_You will receive a confirmation shortly._"
            else:
                return f"❌ Start failed:\n`{result.stderr[:200]}`"
        except subprocess.TimeoutExpired:
            return "❌ Start command timed out"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def _system_off(self, bot) -> str:
        """Stop the system"""
        logger.info("System stop requested via menu")
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
                return "🔴 *Stopping System*\n\nAll components are being stopped...\n\n_You will receive a confirmation shortly._"
            else:
                return f"❌ Stop failed:\n`{result.stderr[:200]}`"
        except subprocess.TimeoutExpired:
            return "❌ Stop command timed out"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def _system_restart(self, bot) -> str:
        """Restart the system"""
        logger.info("System restart requested via menu")
        
        try:
            stop_script = '/home/ubuntu/financial_orchestrator/stop_systemd.sh'
            start_script = '/home/ubuntu/financial_orchestrator/start_systemd.sh'
            
            subprocess.run(['/bin/bash', stop_script], capture_output=True, timeout=15)
            subprocess.run(['/bin/bash', start_script], capture_output=True, timeout=30)
            
            return "🔄 *Restarting System*\n\nSystem is being restarted...\n\n_You will receive a confirmation shortly._"
        except Exception as e:
            return f"❌ Restart error: {str(e)}"


def get_status_keyboard() -> List[List[Dict]]:
    """Get status sub-menu keyboard"""
    return [
        [
            {"text": "📊 Quick Status", "callback_data": "st_quick"},
            {"text": "📈 Detailed", "callback_data": "st_detailed"},
        ],
        [
            {"text": "⬅️ Back to Menu", "callback_data": "main"},
        ],
    ]


def get_info_keyboard() -> List[List[Dict]]:
    """Get info sub-menu keyboard"""
    return [
        [
            {"text": "📁 Workflows", "callback_data": "info_wf"},
            {"text": "💻 Agents", "callback_data": "info_ag"},
        ],
        [
            {"text": "📄 Logs", "callback_data": "info_logs"},
            {"text": "🔔 Alerts", "callback_data": "info_alerts"},
        ],
        [
            {"text": "⬅️ Back to Menu", "callback_data": "main"},
        ],
    ]
