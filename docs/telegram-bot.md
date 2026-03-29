# Telegram Watchtower Bot

Real-time monitoring bot (@NkhekheAlphaBot) for the Financial Orchestrator system with modern inline keyboard UI.

## Features

- **Admin-only Access**: Only authorized chat IDs can interact
- **Modern UI**: Inline keyboard with clickable buttons
- **Real-time Monitoring**: Log tailing and event monitoring
- **Proactive Alerts**: Automatic notifications for ERROR/CRITICAL events
- **Resource Monitoring**: Memory, CPU, disk usage tracking
- **Health Reports**: 5-minute heartbeat status updates
- **Command Interface**: Rich set of management commands

## Main Menu UI

When you send `/start` or `/menu`, you get a modern inline keyboard:

```
[🟢 System On] [🔴 System Off] [🔄 Restart]
[📊 Status] [📈 Metrics] [🔔 Alerts]
[📁 Workflows] [💻 Agents] [📄 Logs]
[🔒 Hide Menu]
```

Click any button to execute that action!

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TELEGRAM BOT                             │
│                                                             │
│  User ───► /menu ───► Bot Menu (Inline Keyboard)          │
│              │                                              │
│              ▼                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              BOT CONTROLLER                          │   │
│  │  • Polling (5s interval)                            │   │
│  │  • Admin Security (chat_id filter)                 │   │
│  │  • Callback Query Handler                           │   │
│  │  • Inline Keyboard Support                          │   │
│  └─────────────────────────────────────────────────────┘   │
│              │                                              │
│    ┌─────────┼─────────┬──────────┐                        │
│    ▼         ▼         ▼          ▼                        │
│  ┌────┐  ┌──────┐  ┌────────┐  ┌──────────┐                │
│  │Log │  │Event │  │Health │  │Resource  │                │
│  │Tailer│  │Monitor│  │Checker│  │Monitor  │                │
│  └────┘  └──────┘  └────────┘  └──────────┘                │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           NOTIFICATION SYSTEM                        │   │
│  │  • Risk Alerts  • Workflow Events  • System Health  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Available Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `/start` | - | Welcome message + main menu |
| `/menu` | - | Show main menu anytime |
| `/hide` | - | Hide inline keyboard |
| `/systemon` | - | Start all 5 components |
| `/systemoff` | - | Stop all 5 components |
| `/sys` | - | Quick status check |
| `/status` | `/s` | Get system status overview |
| `/metrics` | `/m` | Show detailed system metrics |
| `/workflows` | `/wf` | List active workflows and status |
| `/agents` | `/ag` | List all agents and their status |
| `/logs` | `/log` | Get recent log entries |
| `/alerts` | `/a` | Show recent alerts |
| `/help` | `/h`, `/?` | Show help message |

## Configuration

Edit `telegram_watchtower/config.yaml`:

```yaml
telegram:
  enabled: true
  bot_token: "your_bot_token_here"
  allowed_chat_ids:
    - 7361240735  # Your chat ID
  admin_chat_ids:
    - 7361240735

watchtower:
  name: "Financial Orchestrator Watch Tower"
  version: "1.0.0"
  
  polling:
    interval_seconds: 2
    long_polling_timeout: 5
    
  log_files:
    - path: "/path/to/logs/risk_monitor.log"
      name: "Risk Monitor"
      event_patterns:
        - "ALERT"
        - "WARNING"
        - "CRITICAL"
        - "ERROR"
        
  resource_limits:
    memory_threshold_percent: 85
    cpu_threshold_percent: 90
    disk_threshold_percent: 90
    
  notifications:
    risk_alerts: true
    workflow_status: true
    system_health: true
    agent_events: true
    health_reports: true
    
  health_check:
    enabled: true
    interval_seconds: 300  # 5 minutes
```

## Getting Your Bot Token

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Follow prompts to name your bot
4. Copy the token (format: `123456789:ABCdef...`)

## Getting Your Chat ID

1. Open Telegram and search for **@userinfobot**
2. Send `/start`
3. Note your numeric chat ID

## Setting Up the Bot

### Method 1: Interactive Setup
```bash
./setup_telegram_bot.sh
```

### Method 2: Manual Configuration

1. Edit `telegram_watchtower/config.yaml`:
```yaml
telegram:
  bot_token: "8748820504:AAEoIEzrFLIXD2w9H9in5V_2yVd15le3Qx4"
  allowed_chat_ids:
    - 7361240735
  admin_chat_ids:
    - 7361240735
```

2. Reset Telegram offset (if restarting):
```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates?offset=-1"
```

## Running the Bot

### Manual Start
```bash
cd /home/ubuntu/financial_orchestrator
./telegram_watchtower/start_watchtower.sh
```

### Background with nohup
```bash
nohup python3 telegram_watchtower/bot_controller.py > logs/bot.log 2>&1 &
```

### Systemd Service (Production)

1. Install the service:
```bash
cd telegram_watchtower
sudo ./install_service.sh
```

2. Start the service:
```bash
sudo systemctl start telegram-watchtower
```

3. Enable on boot:
```bash
sudo systemctl enable telegram-watchtower
```

4. Check status:
```bash
sudo systemctl status telegram-watchtower
```

## Service File Location

```
/etc/systemd/system/telegram-watchtower.service
```

Content:
```ini
[Unit]
Description=Financial Orchestrator Telegram Watch Tower
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/financial_orchestrator
ExecStart=/usr/bin/python3 /home/ubuntu/financial_orchestrator/telegram_watchtower/bot_controller.py
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/financial_orchestrator/logs/telegram_watchtower.log
StandardError=append:/home/ubuntu/financial_orchestrator/logs/telegram_watchtower.log

[Install]
WantedBy=multi-user.target
```

## Log Patterns

The bot monitors log files for specific patterns and sends alerts:

| Pattern | Severity | Action |
|---------|----------|--------|
| `ERROR` | High | Immediate alert |
| `CRITICAL` | Critical | Immediate alert + ping |
| `ALERT` | High | Immediate alert |
| `WARNING` | Medium | Queue for summary |
| `FAILED` | High | Immediate alert |

## Monitoring Scope

### System Health
- Agent availability
- Workflow status
- Validation results

### Log Monitoring
- Risk monitor logs
- Workflow logs
- Optimizer logs

### Resource Monitoring
- Memory usage (>85% threshold)
- Disk usage (>90% threshold)
- CPU usage (>90% threshold)

## Troubleshooting

### Bot Not Responding

1. Check if bot is running:
```bash
ps aux | grep bot_controller
```

2. Check logs:
```bash
tail -f logs/telegram_watchtower.log
```

3. Verify token:
```bash
curl "https://api.telegram.org/bot<TOKEN>/getMe"
```

### Duplicate Messages

Reset the Telegram offset:
```bash
curl "https://api.telegram.org/bot<TOKEN>/getUpdates?offset=-1"
```

### Unauthorized User

1. Get their chat ID from @userinfobot
2. Add to `allowed_chat_ids` in config.yaml
3. Restart the bot

### Connection Timeout

Increase polling timeout in config:
```yaml
polling:
  long_polling_timeout: 30  # seconds
```

## Memory Optimization

The bot is designed for minimal resource usage:

- Target: <50MB memory
- Target: <5% CPU
- Max log buffer: 10MB (configurable)
- Cleanup interval: 5 minutes (configurable)

## Security

- Admin-only commands
- Chat ID validation on every request
- No sensitive data in logs
- UTF-8 encoding for all messages
