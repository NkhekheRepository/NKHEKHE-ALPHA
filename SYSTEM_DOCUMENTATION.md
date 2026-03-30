# NKHEKHE ALPHA - Autonomous Quant Trading System

## Overview

NKHEKHE ALPHA is a comprehensive autonomous quantitative trading system designed for Binance Futures with 75x leverage capability. It combines traditional technical analysis with modern machine learning (HMM, PPO) for intelligent market regime detection and adaptive strategy switching.

**Repository**: https://github.com/NkhekheRepository/NKHEKHE-ALPHA

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        NKHEKHE ALPHA TRADING SYSTEM                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     15-LAYER MODULAR ARCHITECTURE                    │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                       │   │
│  │  Layer 1: DATA          - Binance WebSocket, REST API              │   │
│  │  Layer 2: FEATURES      - ATR, ADX, RSI, MACD, Bollinger            │   │
│  │  Layer 3: STRATEGY      - CtaTemplate, Signal Generation            │   │
│  │  Layer 4: INTELLIGENCE  - HMM, PPO, Uncertainty, Exploration       │   │
│  │  Layer 5: SCORING       - Trade opportunity scoring                  │   │
│  │  Layer 6: RISK          - 75x Leverage, Correlation, Portfolio      │   │
│  │  Layer 7: EXECUTION     - VNPY Order Management                     │   │
│  │  Layer 8: MEMORY        - PostgreSQL + Redis                        │   │
│  │  Layer 9: SELF-HEALING  - Auto-restart, Fallbacks                  │   │
│  │  Layer 10: ADAPTIVE     - Regime Detection, Online Training         │   │
│  │  Layer 11: EVENTS       - Event Bus, Layer-to-Layer Comms          │   │
│  │  Layer 12: UNCERTAINTY  - Mean +/- Variance Predictions            │   │
│  │  Layer 13: EXPLORATION  - Adaptive Epsilon-Greedy                  │   │
│  │  Layer 14: VALIDATION   - Walk-Forward, Monte Carlo, OOS          │   │
│  │  Layer 15: EVOLUTION    - Genetic Algorithm Strategy Opt           │   │
│  │                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     SUPPORTING SYSTEMS                               │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                       │   │
│  │  • Telegram Watchtower (@NkhekheAlphaBot)                          │   │
│  │  • Flask Dashboard (Port 8080)                                      │   │
│  │  • Risk Monitor                                                      │   │
│  │  • Health Check System                                               │   │
│  │  • Test Suite (test_all_layers.py)                                  │   │
│  │                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 15-Layer Architecture

### Layer 1: Data Layer
**Location**: `paper_trading/layers/layer1_data/`

Connects to Binance Futures for real-time market data.

| Component | Description |
|-----------|-------------|
| `binance_client.py` | WebSocket client for real-time price streams |
| `binance_futures.py` | Futures-specific data client |
| `binance_live.py` | Live trading execution |
| `normalizer.py` | Data cleaning and standardization |
| `fallback.py` | REST API fallback when WebSocket fails |

**Configuration**:
- WebSocket: `wss://stream.binance.com:9443`
- REST API: `https://api.binance.com`
- Testnet: `https://testnet.binancefuture.com`

---

### Layer 2: Features Layer
**Location**: `paper_trading/layers/layer2_features/`

Technical indicator calculation pipeline.

| Indicator | Description | Parameters |
|-----------|-------------|-------------|
| **ATR** | Average True Range - Volatility measure | Period: 14 |
| **ADX** | Average Directional Index - Trend strength | Period: 14 |
| **RSI** | Relative Strength Index - Overbought/Oversold | Period: 14 |
| **MACD** | Moving Average Convergence Divergence | Fast: 12, Slow: 26, Signal: 9 |
| **Bollinger Bands** | Volatility bands | Period: 20, Std: 2 |

**Feature Pipeline** (`feature_pipeline.py`):
```python
class FeaturePipeline:
    def calculate_atr(self, highs, lows, closes, period=14)
    def calculate_adx(self, highs, lows, closes, period=14)
    def calculate_rsi(self, closes, period=14)
    def calculate_macd(self, closes, fast=12, slow=26, signal=9)
    def calculate_bollinger(self, closes, period=20, std_dev=2)
```

---

### Layer 3: Strategy Layer
**Location**: `paper_trading/layers/layer3_strategies/`

Trading signal generation using multiple strategies.

| Strategy | Description | Parameters |
|----------|-------------|-------------|
| **MA Crossover** | Buy when fast MA crosses above slow MA | Fast: 10, Slow: 30 |
| **RSI** | Buy oversold, sell overbought | Period: 14, OB: 70, OS: 30 |
| **Bollinger Bands** | Mean reversion at bands | Period: 20 |
| **Signal Aggregator** | Combines all signals with weighting | Weighted voting |

**Signal Output**:
```python
@dataclass
class TradingSignal:
    symbol: str
    direction: str  # "long" or "short"
    confidence: float  # 0.0 to 1.0
    price: float
    timestamp: datetime
    source: str  # Strategy name
```

---

### Layer 4: Intelligence Layer
**Location**: `paper_trading/layers/layer4_intelligence/`

ML components for market analysis and decision-making.

#### Hidden Markov Model (HMM)
- **Purpose**: Market regime detection
- **States**: Bull, Bear, Volatile, Sideways
- **Library**: `hmmlearn`
- **Features**: Returns, volatility, trend

```python
class HMMRegimeDetector:
    def detect_regime(self, price_data) -> str  # "bull", "bear", "volatile", "sideways"
    def get_transition_probability(self) -> dict
```

#### Proximal Policy Optimization (PPO)
- **Purpose**: Reinforcement learning for decision-making
- **Library**: PyTorch-based implementation
- **Action Space**: Buy, Sell, Hold
- **State Space**: Price, Volume, Indicators, Regime

```python
class PPOAgent:
    def select_action(self, state)
    def update(self, rewards, states, actions)
    def save(self, path)
    def load(self, path)
```

#### Markov Decision Tree
- **Purpose**: Probability-based decision making
- **Max Depth**: 5

#### Self-Learning Engine
- **Purpose**: Online model training
- **Retrain Interval**: 30 minutes
- **Min Samples**: 50

#### Adaptive Learning
- **Purpose**: Strategy switching based on regime
| Regime | Strategy |
|--------|----------|
| Bull | Momentum |
| Bear | Mean Reversion |
| Volatile | Breakout |
| Sideways | RL-Enhanced |

---

### Layer 5: Scoring Layer
**Location**: `paper_trading/layers/layer5_scoring/`

Trade opportunity scoring and filtering.

```python
class TradeScorer:
    def score_signal(self, signal: TradingSignal) -> float:
        # Confidence weighting
        # Risk-adjusted returns
        # Regime alignment
        pass
    
    def filter_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        # Min confidence threshold: 0.6
        # Max daily signals: 10
        pass
```

**Scoring Factors**:
- Signal confidence (40%)
- Regime alignment (30%)
- Risk/reward ratio (20%)
- Historical performance (10%)

---

### Layer 6: Risk Layer
**Location**: `paper_trading/layers/layer2_risk/`

Risk management and position sizing.

| Parameter | Value |
|-----------|-------|
| **Leverage** | 75x |
| **Max Position Size** | 10% of capital |
| **Daily Loss Limit** | 5% |
| **Max Drawdown** | 20% |
| **Stop Loss** | 2% |
| **Take Profit** | 5% |

**Risk Engine** (`risk_engine.py`):
```python
class RiskEngine:
    def check_position_size(self, size: float, capital: float) -> bool
    def calculate_stop_loss(self, entry: float, direction: str) -> float
    def calculate_take_profit(self, entry: float, direction: str) -> float
    def check_daily_loss(self, daily_pnl: float) -> bool
    def calculate_position_size(self, risk: float, capital: float) -> float
```

**Circuit Breaker** (`circuit_breaker.py`):
- Halts trading after 5 consecutive failures
- Auto-resets after 15 minutes
- Triggers on API failures or extreme losses

**Emergency Stop** (`emergency_stop.py`):
- Immediate trading halt
- Closes all open positions
- Notification to Telegram

**Correlation Control** (`correlation_control.py`):
- Rolling correlation matrix computation
- High correlation detection between assets (>0.7)
- Portfolio diversification scoring
- Reduces exposure to highly correlated positions

**Portfolio Optimizer** (`portfolio_optimizer.py`):
- Mean-variance optimization (Markowitz)
- Risk parity allocation
- Kelly criterion position sizing
- Efficient frontier calculation

---

### Layer 7: Execution Layer
**Location**: `paper_trading/layers/layer5_execution/`

Order execution via VNPY and Binance API.

| Order Type | Description |
|------------|-------------|
| **Market** | Immediate execution |
| **Limit** | Price-specified execution |
| **Stop-Loss** | Automatic loss mitigation |
| **Take-Profit** | Profit locking |

**Order Manager** (`order_manager.py`):
```python
class OrderManager:
    def place_order(self, symbol: str, side: str, quantity: float, order_type: str)
    def cancel_order(self, order_id: str)
    def get_position(self, symbol: str) -> Position
    def calculate_pnl(self, symbol: str) -> float
```

**Leverage Handler** (`leverage.py`):
```python
class LeverageHandler:
    def set_leverage(self, symbol: str, leverage: int)
    def get_max_position(self, symbol: str, leverage: int) -> float
```

---

### Layer 8: Memory Layer
**Location**: `paper_trading/layers/layer9_memory/`

Persistent storage using PostgreSQL + Redis.

#### PostgreSQL Schema

**Database**: `nwa45690` (password)

```sql
-- Core Tables
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20),
    direction VARCHAR(10),
    entry_price DECIMAL,
    exit_price DECIMAL,
    quantity DECIMAL,
    pnl DECIMAL,
    status VARCHAR(20),
    opened_at TIMESTAMP,
    closed_at TIMESTAMP
);

CREATE TABLE decisions (
    id SERIAL PRIMARY KEY,
    signal_source VARCHAR(50),
    confidence DECIMAL,
    regime VARCHAR(20),
    action VARCHAR(10),
    reasoning TEXT,
    timestamp TIMESTAMP
);

CREATE TABLE metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(50),
    value DECIMAL,
    timestamp TIMESTAMP
);

CREATE TABLE regime_performance (
    id SERIAL PRIMARY KEY,
    regime VARCHAR(20),
    total_trades INT,
    winning_trades INT,
    avg_pnl DECIMAL,
    period_start TIMESTAMP,
    period_end TIMESTAMP
);

CREATE TABLE strategy_performance (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(50),
    total_signals INT,
    executed_signals INT,
    success_rate DECIMAL,
    avg_pnl DECIMAL
);

CREATE TABLE system_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50),
    severity VARCHAR(20),
    message TEXT,
    timestamp TIMESTAMP
);

CREATE TABLE model_versions (
    id SERIAL PRIMARY KEY,
    model_type VARCHAR(50),
    version INT,
    accuracy DECIMAL,
    trained_at TIMESTAMP,
    parameters JSONB
);

CREATE TABLE price_alerts (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20),
    condition VARCHAR(20),
    target_price DECIMAL,
    triggered BOOLEAN,
    created_at TIMESTAMP
);

CREATE TABLE layer_health (
    id SERIAL PRIMARY KEY,
    layer_name VARCHAR(50),
    status VARCHAR(20),
    last_check TIMESTAMP,
    error_count INT
);

CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20),
    side VARCHAR(10),
    quantity DECIMAL,
    entry_price DECIMAL,
    unrealized_pnl DECIMAL,
    opened_at TIMESTAMP
);
```

#### Redis (Caching)
- Real-time price data
- Session state
- Rate limiting

---

### Layer 9: Self-Healing
**Location**: `paper_trading/layers/layer6_orchestration/`

Automatic recovery from failures.

| Component | Description |
|-----------|-------------|
| **Auto Restart** | Monitors processes, restarts failed components |
| **Circuit Breaker** | Halts on repeated failures |
| **Fallback Mechanisms** | WebSocket → REST API fallback |
| **Error Isolation** | One layer failing doesn't crash system |

**Auto Restart** (`auto_restart.py`):
```python
class AutoRestart:
    def check_component_health(self, component: str) -> bool
    def restart_component(self, component: str) -> bool
    def get_restart_count(self) -> int
```

---

### Layer 10: Adaptive Learning
**Location**: `paper_trading/layers/layer4_intelligence/`

Continuous improvement through regime detection and online training.

| Feature | Description |
|---------|-------------|
| **Regime Detection** | Real-time market state identification |
| **Online Training** | Model updates every 30 minutes |
| **Strategy Switching** | Automatic strategy selection |
| **Performance Tracking** | Per-regime, per-strategy metrics |

```python
class AdaptiveLearning:
    def detect_regime(self, market_data) -> str
    def select_strategy(self, regime: str) -> str
    def train_on_experience(self, trade_result: dict)
    def update_model(self)
```

---

## Orchestrator

**Location**: `paper_trading/orchestrator/trading_orchestrator.py`

Main controller coordinating all 10 layers.

```python
class TradingOrchestrator:
    def __init__(self, config_path: str):
        self.layers = {}
        self.running = False
        
    def initialize_layers(self):
        # Initialize all 10 layers
        pass
    
    def start(self):
        # Start trading loop
        pass
    
    def process_market_data(self, data: dict):
        # Data → Features → Strategy → Intelligence → Scoring → Risk → Execution
        pass
    
    def get_system_status(self) -> dict:
        # Return health of all layers
        pass
```

---

## Configuration

### Main Configuration (`paper_trading/config.yaml`)

```yaml
trading:
  initial_capital: 10000
  leverage: 75
  symbols:
    - BTCUSDT
    - ETHUSDT
    - SOLUSDT
    - BNBUSDT

risk:
  max_position_pct: 0.10
  daily_loss_limit: 0.05
  max_drawdown: 0.20
  stop_loss: 0.02
  take_profit: 0.05
  max_consecutive_losses: 5

strategies:
  ma_crossover:
    fast_period: 10
    slow_period: 30
  rsi:
    period: 14
    overbought: 70
    oversold: 30
  bollinger:
    period: 20
    std_dev: 2

intelligence:
  hmm:
    n_states: 4
    n_iterations: 100
  ppo:
    learning_rate: 0.0003
    gamma: 0.99
    clip_ratio: 0.2

telegram:
  enabled: true
  bot_token: "8748820504:AAEoIEzrFLIXD2w9H9in5V_2yVd15le3Qx4"
  admin_chat_id: "7361240735"

database:
  postgres:
    host: "localhost"
    port: 5432
    database: "nwa45690"
    password: "nwa45690"
  redis:
    host: "localhost"
    port: 6379
```

---

## Telegram Bot (@NkhekheAlphaBot)

**Location**: `telegram_watchtower/`

Real-time monitoring and control.

### Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize bot and show menu |
| `/status` | System health status |
| `/metrics` | Performance metrics |
| `/workflows` | Active workflows |
| `/logs` | Recent log entries |
| `/agents` | Agent statuses |
| `/alerts` | Recent alerts |
| `/help` | Help information |

### Features

- **Real-time Alerts**: Risk warnings, trade notifications
- **Health Checks**: Hourly system reports
- **Log Monitoring**: ERROR/CRITICAL detection
- **Resource Monitoring**: CPU, Memory, Disk alerts
- **Admin Security**: Chat ID filtering

---

## Dashboard

**Location**: `paper_trading/dashboard/app.py`

Flask web interface on port 8080.

**Features**:
- Real-time position tracking
- P&L charts
- Trade history
- System health
- Strategy performance

---

## Starting the System

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL
docker-compose up -d postgres

# Start Redis
docker-compose up -d redis
```

### Run Modes

**Paper Trading**:
```bash
python run_paper_trading.py
```

**Live Trading**:
```bash
python run_live_trading.py
```

**Autonomous Trading**:
```bash
python autonomous_trading.py
```

### System Services
```bash
# Start all components
./start_system.sh

# Stop all components
./stop_system.sh
```

---

## Testing

### Unit Tests
```bash
# VNPY CTA Strategies
python -m pytest vnpy_engine/tests/test_cta_strategies.py -v

# RL Module
python -m pytest vnpy_engine/tests/test_rl_module.py -v

# Integration Tests
python integration_test.py
```

### Test Coverage

| Module | Tests |
|--------|-------|
| CTA Strategies | 19 tests |
| RL Module | 30 tests |
| RL-CT Integration | 10 tests |
| Feature Pipeline | 12 tests |

---

## Security Notes

1. **API Keys**: Store in `.env` file, never commit
2. **Database Password**: `nwa45690` - change in production
3. **Telegram Bot Token**: Keep secure
4. **Rate Limiting**: Implemented for API protection

---

## New Layers (v2.0)

### Layer 11: Event Layer
**Location**: `paper_trading/layers/layer10_events/event_bus.py`

Event-driven communication between all layers.

| Component | Description |
|-----------|-------------|
| `EventBus` | Central message bus for layer-to-layer communication |
| `Event` | Typed event data structure with priority |
| `EventType` | 20+ event types (TRADE_OPENED, RISK_ALERT, SIGNAL_GENERATED, etc.) |

**Features**:
- Publish/subscribe pattern with typed handlers
- Event history and replay
- Filtered subscriptions
- Wildcard subscribers for all events
- Event statistics tracking

### Layer 12: Uncertainty Model
**Location**: `paper_trading/layers/layer4_intelligence/uncertainty_model.py`

Probabilistic predictions with mean +/- variance bounds.

| Rule | Behavior |
|------|----------|
| **High uncertainty** | Reduce position size |
| **Low uncertainty + high expectancy** | Increase position size |
| **Insufficient data** | Minimal position (20% of base) |

**Features**:
- Bayesian-style uncertainty estimation
- Regime-aware variance adjustment (volatile: 1.5x, trending: 0.8x)
- Calibration checking (MAE, MAPE)
- Position size adjustment based on confidence

### Layer 13: Exploration Engine
**Location**: `paper_trading/layers/layer4_intelligence/exploration_engine.py`

Adaptive epsilon-greedy exploration for discovering new market edges.

| Parameter | Value |
|-----------|-------|
| **Base epsilon** | 0.15 |
| **Min epsilon** | 0.02 |
| **Max epsilon** | 0.40 |
| **Exploration size** | 30% of base |

**Behavior**:
- Increases exploration when performance degrades
- Tracks exploration vs exploitation success rates
- Uses smaller capital for exploratory trades
- Adapts exploration rate dynamically

### Layer 14: Model Validation Engine
**Location**: `paper_trading/layers/layer5_validation/model_validator.py`

Continuous verification: "Is my edge still valid?"

| Method | Purpose |
|--------|---------|
| **Walk-Forward** | Train on past, test on recent data |
| **Monte Carlo** | Test if returns differ from random |
| **Out-of-Sample** | Validate on unseen data |
| **Bootstrap CI** | Confidence intervals via resampling |

**Features**:
- Permutation testing for significance
- Statistical significance at p < 0.05
- Automatic risk reduction when edge degrades

### Layer 15: Evolution Engine
**Location**: `paper_trading/layers/layer4_intelligence/evolution_engine.py`

Genetic algorithm for strategy parameter optimization.

| Parameter | Value |
|-----------|-------|
| **Population** | 20 genomes |
| **Mutation rate** | 0.15 |
| **Crossover rate** | 0.70 |
| **Elite count** | 2 |

**Features**:
- Tournament selection of best performers
- Gaussian mutation of strategy parameters
- Dynamic capital allocation based on fitness
- Sharpe + Sortino composite fitness scoring

---

## License

MIT License

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/NkhekheRepository/NKHEKHE-ALPHA/issues
- Telegram: @NkhekheAlphaBot
