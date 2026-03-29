#!/usr/bin/env python3
"""
Health Check Script for Financial Orchestrator
Monitors system health and sends periodic reports to Telegram
"""
import os
import sys
import time
import json
import psutil
import subprocess
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from telegram_notify import send_to_admin, send_alert

COMPONENTS = {
    'telegram_watchtower/bot_controller.py': 'Telegram Bot',
    'monitoring/risk_monitor.py': 'Risk Monitor',
    'validation/validation_engine.py': 'Validation Engine',
    'optimization/agent_optimizer.py': 'Agent Optimizer',
    'workflows/process_workflow.py': 'Workflow Processor'
}

HEALTH_LOG = Path(__file__).parent / 'logs' / 'health_check.log'

def log(message):
    """Log to file and print"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {message}"
    print(line)
    HEALTH_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(HEALTH_LOG, 'a') as f:
        f.write(line + '\n')

def check_component_running(name, pid_file):
    """Check if a component is running"""
    try:
        pid_path = Path(pid_file)
        if pid_path.exists():
            pid = int(pid_path.read_text().strip())
            if psutil.pid_exists(pid):
                process = psutil.Process(pid)
                if process.is_running():
                    mem_mb = process.memory_info().rss / 1024 / 1024
                    cpu_percent = process.cpu_percent(interval=0.1)
                    return {'running': True, 'pid': pid, 'memory_mb': mem_mb, 'cpu_percent': cpu_percent}
        return {'running': False}
    except Exception as e:
        return {'running': False, 'error': str(e)}

def get_system_stats():
    """Get overall system statistics"""
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': psutil.cpu_percent(interval=0.5),
            'memory_percent': memory.percent,
            'memory_used_gb': round(memory.used / (1024**3), 2),
            'memory_total_gb': round(memory.total / (1024**3), 2),
            'disk_percent': disk.percent,
            'disk_used_gb': round(disk.used / (1024**3), 2),
            'disk_total_gb': round(disk.total / (1024**3), 2)
        }
    except Exception as e:
        log(f"Error getting system stats: {e}")
        return None

def check_processes():
    """Check all monitored processes"""
    results = {}
    logs_dir = Path(__file__).parent / 'logs'
    
    for script, name in COMPONENTS.items():
        pid_file = logs_dir / f"{Path(script).stem}.pid"
        result = check_component_running(name, pid_file)
        results[name] = result
    
    return results

def format_health_report(system_stats, component_status):
    """Format health report for Telegram"""
    report = ["📊 *Financial Orchestrator Health Report*"]
    report.append(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    report.append("🖥️ *System Stats:*")
    if system_stats:
        report.append(f"  CPU: {system_stats['cpu_percent']:.1f}%")
        report.append(f"  RAM: {system_stats['memory_percent']:.1f}% ({system_stats['memory_used_gb']}/{system_stats['memory_total_gb']} GB)")
        report.append(f"  Disk: {system_stats['disk_percent']:.1f}% ({system_stats['disk_used_gb']}/{system_stats['disk_total_gb']} GB)")
    else:
        report.append("  ⚠️ Unable to retrieve system stats")
    
    report.append("\n🔧 *Components:*")
    all_running = True
    for name, status in component_status.items():
        if status.get('running'):
            mem = status.get('memory_mb', 0)
            cpu = status.get('cpu_percent', 0)
            report.append(f"  ✅ {name} (PID:{status['pid']}, RAM:{mem:.1f}MB, CPU:{cpu:.1f}%)")
        else:
            report.append(f"  ❌ {name} - NOT RUNNING")
            all_running = False
    
    if all_running:
        report.append("\n🎯 All systems operational")
    else:
        report.append("\n⚠️ Some components need attention")
    
    return '\n'.join(report)

def send_health_check():
    """Perform health check and send report"""
    log("Starting health check...")
    
    system_stats = get_system_stats()
    component_status = check_processes()
    
    report = format_health_report(system_stats, component_status)
    
    if system_stats and all(s.get('running', False) for s in component_status.values()):
        send_to_admin(report)
    else:
        send_alert("Health Check", "WARNING", "Some components not running", report)
    
    log("Health check completed")
    return all(s.get('running', False) for s in component_status.values())

def run_once():
    """Run health check once"""
    return send_health_check()

def run_continuous(interval=300):
    """Run health check continuously"""
    log(f"Starting continuous health monitoring (interval: {interval}s)")
    
    while True:
        try:
            send_health_check()
            time.sleep(interval)
        except KeyboardInterrupt:
            log("Health check stopped by user")
            break
        except Exception as e:
            log(f"Health check error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 300
        run_continuous(interval)
    else:
        run_once()
