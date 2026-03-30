# Paper Trading Engine

Comprehensive autonomous quant trading system with VNPY integration, self-learning capabilities, and 7-layer architecture.

## Overview

The Paper Trading Engine is a production-ready trading system designed for:
- **Backtesting**: Test strategies on historical data
- **Paper Trading**: Simulate live trading without real capital
- **Live Trading**: Connect to Binance for real-money trading

## Architecture

### 7-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PAPER TRADING ENGINE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Layer 7: Command & Control                                          │   │
│  │  • Telegram Bot (@NkhekheAlphaBot)                                 │   │
│  │  • Web Dashboard (Flask)                                           │   │
│  │  • Command Processor                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Layer 6: Orchestration                                              │   │
│  │  • Health Monitor (60s interval)                                  │   │
│  │  • Auto-Restart (on failure)                                       │   │
│  │  • Config Hot-Reload (30s interval)                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Layer 5: Execution                                                  │   │
│  │  • Order Manager (position tracking, P&L)                         │   │
│  │  • Leverage Handler (up to 75x)                                    │   │
│  │  • VNPY MainEngine Integration                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Layer 4: Intelligence                                               │   │
│  │  • Hidden Markov Model (HMM) - Regime Detection                    │   │
│  │  • Markov Decision Tree - Decision Making                          │   │
│  │  • Self-Learning - Online Training                                 │   │
│  │  • Adaptive Learning - Strategy Switching                         │   │
│  │  • Ensemble - Multiple model voting                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Layer 3: Signal Generation                                          │   │
│  │  • MA Crossover (Moving Average)                                   │   │
│  │  • RSI (Relative Strength Index)                                  │   │
│  │  • Signal Aggregator (combine signals)                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Layer 2: Risk Management                                            │   │
│  │  • Risk Engine (position sizing, limits)                          │   │
│  │  • Circuit Breaker (halt on extreme loss)                         │   │
│  │  • Emergency Stop (kill switch)                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Layer 1: Data & Connectivity                                        │   │
│  │  • Binance WebSocket (real-time)                                  │   │
│  │  • REST API Fallback                                               │   │
│  │  • Data Normalizer                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
paper_trading/
├── engine.py                    # Main PaperTradingEngine class
├── config.yaml                  # Trading configuration
├── run_paper_trading.py         # Launcher script
├── telegram_commands.py         # Telegram bot commands
├── dashboard/                   # Web Dashboard
│   ├── app.py                  # Flask application
│   └── templates/
│       └── index.html          # Dashboard UI
└── layers/                      # 7-layer architecture
    ├── __init__.py
    ├── layer1_data/
    │   ├── binance_client.py   # WebSocket client
    │   ├── normalizer.py        # Data normalization
    │   └── fallback.py          # REST fallback
    ├── layer2_risk/
    │   ├── risk_engine.py      # Position sizing & limits
    │   ├── circuit_breaker.py  # Trading halt on loss
    │   └── emergency_stop.py   # Kill switch
    ├── layer3_signals/
    │   ├── ma_crossover.py     # MA strategy
    │   ├── rsi.py              # RSI strategy
    │   └── signal_aggregator.py # Combine signals
    ├── layer4_intelligence/
    │   ├── hmm.py              # Hidden Markov Model
    │   ├── decision_tree.py   # Markov Decision Tree
    │   ├── self_learning.py    # Online training
    │   ├── adaptive_learning.py # Regime detection
    │   └── ensemble.py         # Model ensemble
    ├── layer5_execution/
    │   ├── order_manager.py    # Order management
    │   └── leverage.py         # Leverage handling
    └── layer6_orchestration/
        ├── health_monitor.py   # Health checks
        ├── auto_restart.py     # Auto-restart
        └── config_reload.py    # Hot config reload
```

## Configuration

Edit `paper_trading/config.yaml`:

```yaml
trading:
  initial_capital: 10000
  leverage: 75
  symbols:
    - BTCUSDT
  update_interval: 5
  mode: paper
  enabled: true

risk:
  max_daily_loss_pct: 5
  max_drawdown_pct: 20
  position_size_pct: 10
  stop_loss_pct: 2
  take_profit_pct: 5

strategies:
  - name: "RL_Enhanced"
    class: "RlEnhancedCtaStrategy"
    vt_symbol: "BTCUSDT.BINANCE"
    enabled: true

intelligence:
  hmm:
    enabled: true
    n_states: 4
  self_learning:
    enabled: true
    retrain_interval: 1800
  adaptive:
    enabled: true
```

## Running the System

### Quick Start

```bash
cd /home/ubuntu/financial_orchestrator
python run_paper_trading.py
```

### Components

1. **Paper Trading Engine** - Core trading logic
2. **Web Dashboard** - Real-time monitoring at http://localhost:8080
3. **Telegram Bot** - Control via @NkhekheAlphaBot

### Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Start trading |
| `/stop` | Stop trading |
| `/status` | System status |
| `/balance` | Account balance |
| `/positions` | Open positions |
| `/metrics` | Performance metrics |

## Self-Healing Features

### Auto-Restart
- Automatically restarts on failure
- Configurable restart delay
- Logs all restart events

### Fallback Mechanisms
- WebSocket → REST API fallback
- Graceful degradation
- Connection retry with exponential backoff

### Circuit Breaker
- Halts trading on extreme losses
- Configurable thresholds
- Manual override available

## Self-Learning System

### Online Training
- Retrains models every 30 minutes
- Minimum 100 samples required
- Tracks prediction accuracy

### Regime Detection (HMM)
- Detects market regimes: bull, bear, volatile, sideways
- Automatically switches strategies based on regime
- 4-state Hidden Markov Model

### Adaptive Learning
- Maps regimes to optimal strategies:
  - Bull → MomentumCtaStrategy
  - Bear → MeanReversionCtaStrategy
  - Volatile → BreakoutCtaStrategy
  - Sideways → RlEnhancedCtaStrategy

## Intelligence Layer

### Hidden Markov Model (HMM)
- Uses hmmlearn library
- 4 hidden states for market regimes
- Features: returns, volatility, momentum

### Markov Decision Tree
- Decision tree with Markov property
- Max depth: 5
- Probability-based decisions

### Ensemble
- Combines multiple model predictions
- Weighted voting
- Confidence scoring

## Risk Management

### Position Sizing
- Default: 10% of capital per trade
- Adjustable via config

### Stop Loss
- Default: 2% per trade
- Takes profit at 5%

### Daily Loss Limit
- Max 5% daily loss
- Circuit breaker triggers on breach

### Drawdown Limit
- Max 20% drawdown
- Emergency stop on breach

## VNPY Integration

The engine integrates with VNPY:
- **CtaTemplate**: Base strategy class
- **MainEngine**: Order execution
- **ArrayManager**: Technical indicators
- **BarData**: OHLCV data structures

## Testing

Run the test suite:

```bash
cd /home/ubuntu/financial_orchestrator
/home/ubuntu/financial_orchestrator/venv/bin/python -m pytest vnpy_engine/tests/ -v
```

### Test Results

| Test File | Tests | Status |
|-----------|-------|--------|
| test_cta_strategies.py | 19 | ✅ PASS |
| test_rl_cta_integration.py | 10 | ✅ PASS |
| test_rl_module.py | 30 | ✅ PASS |
| test_validate.py | 1 | ✅ PASS |
| **Total** | **60** | **✅ PASS** |

## Dependencies

Required packages (in requirements.txt):
- vnpy - Trading engine
- scikit-learn - ML algorithms
- hmmlearn - Hidden Markov Models
- flask - Web dashboard
- python-telegram-bot - Telegram integration
- numpy, pandas - Data processing
- websocket-client - WebSocket connections

## Deployment

### Production Setup

1. **Systemd Service**:
   ```bash
   sudo cp paper_trading/paper-trading.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable paper-trading
   sudo systemctl start paper-trading
   ```

2. **Environment Variables**:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_token"
   export BINANCE_API_KEY="your_key"
   export BINANCE_SECRET="your_secret"
   ```

### Monitoring

- Web Dashboard: http://localhost:8080
- Telegram: @NkhekheAlphaBot
- Logs: `logs/paper_trading.log`

## Troubleshooting

### Layer-by-Layer Debugging

Each layer can be troubleshot independently:

1. **Layer 1 (Data)**: Check WebSocket connection
2. **Layer 2 (Risk)**: Review risk limits in config
3. **Layer 3 (Signals)**: Check signal indicators
4. **Layer 4 (Intelligence)**: Review ML model logs
5. **Layer 5 (Execution)**: Check order manager status
6. **Layer 6 (Orchestration)**: Review health monitor
7. **Layer 7 (Command)**: Check Telegram bot

### Common Issues

| Issue | Solution |
|-------|----------|
| WebSocket disconnects | Check network, auto-reconnect enabled |
| High drawdown | Review risk limits, reduce position size |
| Model drift | Self-learning will retrain automatically |
| Order failures | Check leverage limits, sufficient balance |

## License

MIT License - see LICENSE file for details.
