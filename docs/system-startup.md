# System Startup Guide

This guide explains how to start, stop, and manage the Financial Orchestrator system.

## Quick Start

```bash
# Start all components
./start_system.sh

# Stop all components
./stop_system.sh
```

## Startup Options

### Option 1: Shell Scripts (Recommended for development)

```bash
# Start everything
./start_system.sh

# Check status
ps aux | grep -E "(bot_controller|risk_monitor|validation_engine|agent_optimizer|process_workflow)"

# Stop everything
./stop_system.sh
```

### Option 2: Systemd Service (Recommended for production)

```bash
# Install the service
sudo cp financial-orchestrator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable financial-orchestrator

# Start the service
sudo systemctl start financial-orchestrator

# Check status
sudo systemctl status financial-orchestrator

# Stop the service
sudo systemctl stop financial-orchestrator
```

## Components

The system consists of 5 main components:

| Component | Description | Log File |
|-----------|-------------|----------|
| Telegram Bot | Real-time monitoring bot (@NkhekheAlphaBot) | `logs/telegram.log` |
| Risk Monitor | Risk score monitoring and alerts | `logs/risk.log` |
| Validation Engine | Workflow validation | `logs/validation.log` |
| Agent Optimizer | Performance optimization | `logs/optimizer.log` |
| Workflow Processor | Workflow execution | `logs/workflow.log` |

## Telegram Notifications

The system sends notifications to Telegram when:
- **System starts** - List of all running components
- **System stops** - Confirmation of shutdown
- **Risk alerts** - HIGH/CRITICAL risk levels triggered
- **Component errors** - Errors detected in any component

### Notification Recipients

- Admin Chat ID: `7361240735`

### Alert Levels

| Level | Emoji | Description |
|-------|-------|-------------|
| CRITICAL | 🚨 | Kill switch triggered, immediate action required |
| ERROR | ❌ | Component error, needs attention |
| WARNING | ⚠️ | Warning condition, monitor closely |
| INFO | ℹ️ | Informational message |

## Managing Individual Components

### Start a specific component:

```bash
# Telegram Bot
nohup python3 telegram_watchtower/bot_controller.py > logs/telegram.log 2>&1 &

# Risk Monitor
nohup python3 monitoring/risk_monitor.py > logs/risk.log 2>&1 &

# Validation Engine
nohup python3 validation/validation_engine.py > logs/validation.log 2>&1 &

# Agent Optimizer
nohup python3 optimization/agent_optimizer.py > logs/optimizer.log 2>&1 &

# Workflow Processor
nohup python3 workflows/process_workflow.py > logs/workflow.log 2>&1 &
```

### Stop a specific component:

```bash
# Find the PID
ps aux | grep process_name

# Kill it
kill <PID>
```

## Log Files

All components log to `/home/ubuntu/financial_orchestrator/logs/`:

```
logs/
├── telegram.log          # Telegram bot logs
├── risk.log              # Risk monitor logs
├── validation.log        # Validation engine logs
├── optimizer.log         # Agent optimizer logs
├── workflow.log          # Workflow processor logs
├── telegram_watchtower.log  # Telegram polling logs
└── e2e_test_results.json    # Test results
```

### View logs in real-time:

```bash
# All components
tail -f logs/*.log

# Specific component
tail -f logs/telegram.log

# Errors only
grep -i error logs/*.log
```

## Health Checks

### Check if all components are running:

```bash
./start_system.sh  # Will report status
```

### Check with PID files:

```bash
ls -la logs/*.pid
```

### Check system resources:

```bash
# Memory usage
free -h

# Disk usage
df -h

# Running processes
ps aux | grep python
```

## Troubleshooting

### Components won't start

1. Check Python is installed: `python3 --version`
2. Check dependencies: `pip3 install -r requirements.txt`
3. Check log files for errors: `tail logs/*.log`

### Telegram notifications not working

1. Verify bot token in `telegram_watchtower/config.yaml`
2. Check if bot is active: Send `/start` to @NkhekheAlphaBot
3. Check network connectivity: `curl -I https://api.telegram.org`

### High resource usage

- Memory: Check if components have memory leaks in logs
- CPU: Normal polling uses <5% CPU
- Disk: Rotate logs if they get too large

## systemd Service Commands

```bash
# Start on boot
sudo systemctl enable financial-orchestrator

# Disable autostart
sudo systemctl disable financial-orchestrator

# View logs
sudo journalctl -u financial-orchestrator -f

# Restart after config changes
sudo systemctl restart financial-orchestrator
```
