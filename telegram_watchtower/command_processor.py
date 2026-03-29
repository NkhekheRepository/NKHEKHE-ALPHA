#!/usr/bin/env python3
"""
Command Processor for Telegram Watch Tower
Handles user commands and generates responses
"""

import logging
import json
import os
import sys
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger('CommandProcessor')

class CommandProcessor:
    def __init__(self, config: Dict):
        self.config = config
        self.commands = config.get('watchtower', {}).get('commands', [])
        
        self.command_handlers = {
            '/start': self.cmd_start,
            '/hello': self.cmd_start,
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
            '/help': self.cmd_help,
            '/h': self.cmd_help,
            '/?': self.cmd_help,
        }
    
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
    
    def cmd_start(self, chat_id: int, text: str, bot) -> str:
        """Handle /start command"""
        response = [
            "*Welcome to Financial Orchestrator Watch Tower!*\n",
            f"\ud83c\udfe2 Bot: {self.config['watchtower']['name']}",
            f"\ud83d\udcbb Version: {self.config['watchtower']['version']}\n",
            "\ud83d\udcfa *Quick Commands:*",
            "  /status - System status",
            "  /metrics - System metrics",
            "  /logs - Recent logs",
            "  /help - Full help\n",
            "I will notify you of system events, alerts, and workflow updates in real-time!"
        ]
        return "\n".join(response)
    
    def cmd_status(self, chat_id: int, text: str, bot) -> str:
        """Get system status"""
        status = bot.get_status()
        metrics = bot.get_system_metrics()
        
        uptime_str = self._format_uptime(status.get('uptime_seconds', 0))
        
        response = [
            f"*System Status*\n",
            f"\u2139\ufe0f *Name:* {status['name']}",
            f"\u2b50 *Version:* {status['version']}",
            f"\u2705 *Status:* {status['status']}",
            f"\u23f1 *Uptime:* {uptime_str}",
            f"\n*Memory Usage:*",
            f"  Total: {metrics['memory'].get('total_mb', 0):.0f} MB",
            f"  Used: {metrics['memory'].get('used_mb', 0):.0f} MB",
            f"  Available: {metrics['memory'].get('available_mb', 0):.0f} MB",
            f"  Usage: {metrics['memory'].get('usage_percent', 0):.1f}%",
            f"\n*Alerts:* {status.get('alerts_count', 0)}"
        ]
        
        return "\n".join(response)
    
    def cmd_workflows(self, chat_id: int, text: str, bot) -> str:
        """Get active workflows"""
        workflow_file = '/home/ubuntu/financial_orchestrator/logs/e2e_workflow_state.json'
        
        response = ["*Active Workflows*\n"]
        
        if os.path.exists(workflow_file):
            try:
                with open(workflow_file, 'r') as f:
                    workflow = json.load(f)
                
                response.append(f"\u2b50 *Workflow ID:* {workflow.get('workflow_id', 'N/A')}")
                response.append(f"\u2705 *Status:* {workflow.get('status', 'unknown')}")
                response.append(f"\ud83d\udcbb *Progress:* {workflow.get('progress_percentage', 0)}%")
                response.append(f"\ud83d\udd52 *Phases:* {len(workflow.get('phases', []))}")
                
                if workflow.get('phases'):
                    response.append(f"\n*Phases:*")
                    for phase in workflow['phases']:
                        status_icon = "\u2705" if phase.get('status') == 'completed' else "\u23f3"
                        response.append(f"  {status_icon} {phase.get('name', 'Unknown')}")
            except Exception as e:
                response.append(f"\u274c Error loading workflow: {e}")
        else:
            response.append(f"\n\ud83d\udcc4 No workflow state file found")
        
        return "\n".join(response)
    
    def cmd_agents(self, chat_id: int, text: str, bot) -> str:
        """Get agent statuses"""
        try:
            from optimization.agent_optimizer import AgentOptimizer
            optimizer = AgentOptimizer()
            status = optimizer.get_optimization_status()
            
            response = [
                "*Agent Status*\n",
                f"\u2705 *Optimization Active:* {status['optimization_active']}",
                f"\ud83d\udcbb *Agents Tracked:* {status['agents_tracked']}",
                f"\ud83d\udcc2 *Workflows Tracked:* {status['workflows_tracked']}",
            ]
            
            if status['agents_tracked'] > 0:
                response.append(f"\n*Agent Details:*")
                for agent_id, data in optimizer.agent_performance.items():
                    response.append(f"  \u2022 {agent_id}: {data['tasks_completed']} tasks")
            
        except Exception as e:
            response = [f"*Agent Status*\n\u274c Error: {e}"]
        
        return "\n".join(response)
    
    def cmd_logs(self, chat_id: int, text: str, bot) -> str:
        """Get recent logs"""
        parts = text.strip().split()
        source_filter = None
        if len(parts) > 1:
            source_filter = parts[1]
        
        logs = []
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
                                logs.append(f"*{log_file}:*")
                                for line in recent:
                                    logs.append(f"  `{line[:100]}...`" if len(line) > 100 else f"  `{line}`")
                    except Exception as e:
                        logs.append(f"*{log_file}:* Error: {e}")
        
        if not logs:
            return "*Recent Logs*\n\ud83d\udcc1 No logs found"
        
        return "\n".join(logs[:20])
    
    def cmd_metrics(self, chat_id: int, text: str, bot) -> str:
        """Get system metrics"""
        metrics = bot.get_system_metrics()
        
        response = [
            "*System Metrics*\n",
            f"\u23f1 *Uptime:* {metrics.get('uptime', 'unknown')}",
            f"\n*Memory:*",
            f"  Total: {metrics['memory'].get('total_mb', 0):.0f} MB",
            f"  Used: {metrics['memory'].get('used_mb', 0):.0f} MB",
            f"  Available: {metrics['memory'].get('available_mb', 0):.0f} MB",
            f"  Usage: {metrics['memory'].get('usage_percent', 0):.1f}%",
        ]
        
        return "\n".join(response)
    
    def cmd_alerts(self, chat_id: int, text: str, bot) -> str:
        """Get recent alerts"""
        if bot.event_monitor:
            summary = bot.event_monitor.get_event_summary()
            
            response = [
                "*Recent Alerts*\n",
                f"\ud83d\udd14 *Total Events:* {summary['total_events']}",
            ]
            
            for event_type, count in summary['alert_counts'].items():
                if count > 0:
                    response.append(f"  \u2022 {event_type}: {count}")
            
            if summary['recent_events']:
                response.append(f"\n*Latest Events:*")
                for event in summary['recent_events'][-3:]:
                    emoji = self._get_severity_emoji(event.get('severity', 'info'))
                    response.append(f"  {emoji} {event['type']}: {event['message'][:50]}...")
        else:
            response = ["*Recent Alerts*\n\ud83d\udd14 No event monitor available"]
        
        return "\n".join(response)
    
    def cmd_help(self, chat_id: int, text: str, bot) -> str:
        """Get help message"""
        response = [
            "*Financial Orchestrator Watch Tower*\n",
            f"Version: {self.config['watchtower']['version']}\n",
            "*Available Commands:*\n",
            "\ud83d\udccb `/status` - System status",
            "\ud83d\udcc2 `/workflows` - Active workflows",
            "\ud83d\udcbb `/agents` - Agent statuses",
            "\ud83d\udcc4 `/logs` - Recent logs",
            "\ud83d\udca1 `/metrics` - System metrics",
            "\ud83d\udd14 `/alerts` - Recent alerts",
            "\ud83d\udcfa `/help` - Show this help",
            "\n*Shortcuts:* `/s`, `/wf`, `/ag`, `/m`, `/a`, `/h`"
        ]
        
        return "\n".join(response)
    
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
            'critical': '\u26a0\ufe0f',
            'warning': '\u1f7e1',
            'error': '\u274c',
            'info': '\u2139\ufe0f'
        }.get(severity, '\u2139\ufe0f')
