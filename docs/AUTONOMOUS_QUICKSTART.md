# Autonomous Trading Bot - Quick Start Guide

## Prerequisites

| Requirement | Description |
|-------------|-------------|
| Python 3.12+ | With venv support |
| Telegram Account | For bot notifications |
| Binance Testnet | For testing (recommended) |
| Git | For cloning repository |

## Setup Steps

### 1. Clone Repository
```bash
git clone https://github.com/NkhekheRepository/financial_orchestrator.git
cd financial_orchestrator
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env`:
```
# Binance API (Get from https://testnet.binancefuture.com)
BINANCE_API_KEY=your_testnet_api_key
BINANCE_SECRET_KEY=your_testnet_secret_key
BINANCE_TESTNET=true

# Telegram Bot Token
TELEGRAM_BOT_TOKEN=your_bot_token
ADMIN_CHAT_IDS=your_chat_id
```

### 5. Start Telegram Bot (Optional)
```bash
cd telegram_watchtower
./start_watchtower.sh start
```

### 6. Start Autonomous Trading
```bash
cd /home/ubuntu/financial_orchestrator
nohup ./venv/bin/python3 -u autonomous_trading.py > logs/autonomous_trading.log 2>&1 &
```

## Commands

### Start Trading Bot
```bash
nohup ./venv/bin/python3 -u autonomous_trading.py > logs/autonomous_trading.log 2>&1 &
```

### Stop Trading Bot
```bash
pkill -f "autonomous_trading.py"
```

### Check Status
```bash
ps aux | grep autonomous_trading
```

### View Logs
```bash
tail -f logs/autonomous_trading.log
```

## Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/trade` | Trading status |
| `/balance` | Check balance |
| `/positions` | Open positions |
| `/long [qty]` | Open LONG position |
| `/short [qty]` | Open SHORT position |
| `/close` | Close position |

## Reports

### 30-Second Decision Reports
The bot sends detailed decision reports every 30 seconds including:
- Current price and regime
- AI decision process breakdown
- Position status and PnL
- Learning progress

### Daily Performance Reports
Sent at midnight with:
- Total trades and win rate
- Trade history with PnL
- Learning insights
- Regime performance
- Adaptation status

## Trading Parameters

| Parameter | Value |
|-----------|-------|
| Max Daily Trades | 5 |
| Stop Loss | 2% |
| Take Profit | 5% |
| Confidence Threshold | 60% |
| Leverage | 75x |
| Update Interval | 30 seconds |

## Troubleshooting

### Bot Not Responding
```bash
# Check if running
ps aux | grep autonomous_trading

# Check logs
tail -50 logs/autonomous_trading.log

# Restart
pkill -f "autonomous_trading.py"
nohup ./venv/bin/python3 -u autonomous_trading.py > logs/autonomous_trading.log 2>&1 &
```

### Telegram Not Receiving Messages
```bash
# Check bot is running
ps aux | grep bot_controller

# Restart Telegram bot
cd telegram_watchtower
./start_watchtower.sh restart
```

### API Connection Issues
```bash
# Check Binance connectivity
curl https://testnet.binancefuture.com/fapi/v1/ping

# Verify API keys in .env
cat .env | grep BINANCE
```

### Reset Daily Counters
The bot automatically resets at midnight. To manually reset:
```bash
# Stop the bot
pkill -f "autonomous_trading.py"

# Edit autonomous_trading.py to reset counters (last_reset_date)
# Or wait for midnight reset
```

## File Locations

| File | Purpose |
|------|---------|
| `autonomous_trading.py` | Main trading bot |
| `logs/autonomous_trading.log` | Trading logs |
| `telegram_watchtower/` | Telegram bot |
| `paper_trading/layers/` | ML and trading layers |
| `.env` | API credentials |

## Safety

- Always test with testnet first
- Max 5 trades per day limits risk
- Stop loss at 2% protects capital
- Circuit breaker prevents excessive losses

## Support

- GitHub Issues: https://github.com/NkhekheRepository/financial_orchestrator/issues
- Telegram: @NkhekheAlphaBot
