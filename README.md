# Financial Orchestrator

A comprehensive multi-agent AI system for quantitative research and financial analysis with persistent memory, real-time monitoring, and workflow automation.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FINANCIAL ORCHESTRATOR                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     TELEGRAM WATCHTOWER (@NkhekheAlphaBot)           │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌───────────┐ │   │
│  │  │  /status   │  │  /metrics    │  │  /workflows │  │  /logs    │ │   │
│  │  │  /agents   │  │  /alerts     │  │  /help      │  │  /start   │ │   │
│  │  └─────────────┘  └──────────────┘  └─────────────┘  └───────────┘ │   │
│  │           │               │                │                │       │   │
│  │           └───────────────┴────────────────┴────────────────┘       │   │
│  │                              │                                          │   │
│  │  ┌──────────────────────────┴───────────────────────────────────┐   │   │
│  │  │                    BOT CONTROLLER                               │   │   │
│  │  │  • Polling (2s interval)  • Admin Security (chat_id filter)   │   │   │
│  │  │  • Log Tailing           • Proactive Alerts                   │   │   │
│  │  │  • Health Checks (hourly) • Resource Monitoring               │   │   │
│  │  └────────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         PERSISTENT MEMORY                           │   │
│  │  ┌────────────────┐  ┌──────────────────┐  ┌─────────────────────┐  │   │
│  │  │ agent_definitions│  │ execution_history│  │optimization_knowledge││   │
│  │  │  • ai_engineer │  │  • session logs  │  │  • agent learnings │  │   │
│  │  │  • data_eng.   │  │  • phase status  │  │  • performance     │  │   │
│  │  │  • api_tester  │  │  • metrics       │  │  • promotions      │  │   │
│  │  │  • finance    │  │  • lessons       │  │                    │  │   │
│  │  └────────────────┘  └──────────────────┘  └─────────────────────┘  │   │
│  │  ┌────────────────────┐  ┌─────────────────────────────────────┐   │   │
│  │  │ workflow_templates │  │         risk_scoring_history        │   │   │
│  │  │  • quant_research  │  │  • historical risk scores            │   │   │
│  │  │  • custom workflows│  │  • alert history                     │   │   │
│  │  └────────────────────┘  └─────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         MULTI-AGENT SYSTEM                          │   │
│  │                                                                      │   │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │   │
│  │  │ AI ENGINEER  │◄──►│DATA ENGINEER │◄──►│API TESTER    │        │   │
│  │  │              │    │              │    │              │        │   │
│  │  │ • Qlib       │    │ • OpenBB     │    │ • Endpoint   │        │   │
│  │  │ • TensorFlow │    │ • Data clean │    │ • Load test  │        │   │
│  │  │ • Models     │    │ • Features   │    │ • Validation │        │   │
│  │  └──────────────┘    └──────────────┘    └──────────────┘        │   │
│  │          │                  │                    │                  │   │
│  │          └──────────────────┴────────────────────┘                  │   │
│  │                             │                                        │   │
│  │                      ┌──────▼──────┐                                 │   │
│  │                      │FINANCE TRACKER│                                │   │
│  │                      │              │                                │   │
│  │                      │• Portfolio   │                                │   │
│  │                      │• Risk metrics│                                │   │
│  │                      │• Compliance  │                                │   │
│  │                      └─────────────┘                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│          ┌───────────────────────────┼───────────────────────────┐         │
│          │                           │                           │         │
│          ▼                           ▼                           ▼         │
│  ┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐   │
│  │  WORKFLOW ENGINE │    │  RISK MONITOR     │    │ VALIDATION ENGINE │   │
│  │                   │    │                   │    │                   │   │
│  │ • Phase execution│    │ • Risk scoring    │    │ • Schema validate │   │
│  │ • Task routing   │    │ • Threshold alerts│    │ • Business rules │   │
│  │ • State persist  │    │ • Real-time watch │    │ • Quality checks  │   │
│  │ • Progress track │    │ • VaR monitoring │    │ • Model testing   │   │
│  └───────────────────┘    └───────────────────┘    └───────────────────┘   │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      AGENT OPTIMIZER                                │   │
│  │  • Performance tracking  • Workload balancing                       │   │
│  │  • Agent promotion       • Failure detection                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## System Components

### 7. Paper Trading Engine
Autonomous quant trading system with VNPY integration, self-learning, and 7-layer architecture:

**Architecture:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PAPER TRADING ENGINE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 7: Command & Control (Telegram Bot, Web Dashboard)                  │
│ Layer 6: Orchestration (Health Monitor, Auto-Restart, Config Reload)      │
│ Layer 5: Execution (Order Manager, Leverage Handler)                       │
│ Layer 4: Intelligence (HMM, Decision Tree, Self-Learning, Ensemble)      │
│ Layer 3: Signal Generation (MA Crossover, RSI, Aggregator)                 │
│ Layer 2: Risk Management (Risk Engine, Circuit Breaker, Emergency Stop)    │
│ Layer 1: Data & Connectivity (Binance WebSocket, REST Fallback)            │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Features:**
- 75x leverage for maximum profit potential
- Self-healing (auto-restart, fallbacks)
- Self-learning (online training)
- Adaptive learning (regime detection with HMM)
- VNPY integration (CtaTemplate, MainEngine, ArrayManager)

**Quick Start:**
```bash
python run_paper_trading.py
```

**Test Results:** 60/60 tests passed

---

### 1. Multi-Agent System
Four specialized AI agents working collaboratively:

| Agent | Purpose | Tools/Frameworks |
|-------|---------|------------------|
| **AI Engineer** | Quantitative model development | Qlib, TensorFlow, PyTorch, XGBoost |
| **Data Engineer** | Data ingestion and processing | OpenBB, Pandas, Feature engineering |
| **API Tester** | Endpoint validation and load testing | Request testing, Performance metrics |
| **Finance Tracker** | Portfolio and risk monitoring | Risk metrics, Compliance checks |

### 2. Persistent Memory System
File-based persistent storage for agent knowledge:

```
memory/
├── agent_definitions/        # Agent YAML configs
├── execution_history/        # Session logs and metrics
├── optimization_knowledge/   # Agent learnings and performance
├── workflow_templates/       # Reusable workflow definitions
├── risk_scoring_history/     # Historical risk scores
├── event_triggers/           # Automated event responses
└── schemas/                 # JSON schema definitions
```

### 3. Workflow Engine
Phase-based workflow execution with task routing:

- **Data Acquisition** → **Feature Engineering** → **Model Development** → **Backtesting** → **Deployment**

### 4. Risk Monitoring
Real-time risk analysis with configurable thresholds:

- Risk scoring algorithm
- VaR (Value at Risk) monitoring
- Drawdown tracking
- Proactive alerts

### 5. Validation Engine
Multi-level validation (basic → standard → strict → paranoid):

- JSON schema validation
- Data quality checks
- Business logic rules
- Model output validation

### 6. Telegram Watchtower
Real-time monitoring bot (@NkhekheAlphaBot) with modern inline keyboard UI:

**Commands:**
| Command | Description |
|---------|-------------|
| `/start` | Welcome message + main menu |
| `/menu` | Show main menu anytime |
| `/hide` | Hide inline keyboard |
| `/systemon` | Start all 5 components |
| `/systemoff` | Stop all 5 components |
| `/sys` | Quick status check |
| `/status` | Detailed system status |
| `/metrics` | System metrics |
| `/workflows` | Active workflows |
| `/agents` | Agent statuses |
| `/logs` | Recent logs |
| `/alerts` | Recent alerts |
| `/help` | Show all commands |

**Main Menu Buttons:**
```
[🟢 System On] [🔴 System Off] [🔄 Restart]
[📊 Status] [📈 Metrics] [🔔 Alerts]
[📁 Workflows] [💻 Agents] [📄 Logs]
[🔒 Hide Menu]
```

**Features:**
- Admin-only access (chat_id protection: 7361240735)
- Modern inline keyboard with clickable buttons
- Proactive alerts for ERROR/CRITICAL events
- Resource monitoring (memory, disk)
- 5-minute health check heartbeats
- Automatic status change notifications

## Directory Structure

```
financial_orchestrator/
├── README.md                    # This file
├── LICENSE                      # MIT License
├── requirements.txt             # Python dependencies
├── setup.sh                     # Main installation script
├── setup_agents.sh              # Agent initialization
├── setup_telegram_bot.sh        # Telegram bot setup
├── .gitignore                   # Git ignore patterns
│
├── agents/                      # Agent configurations
│   ├── ai_engineer_config.yaml
│   ├── data_engineer_config.yaml
│   ├── api_tester_config.yaml
│   └── finance_tracker_config.yaml
│
├── configs/                     # System configurations
│   ├── orchestrator_config.yaml
│   ├── agent_template.yaml
│   └── risk_scoring.yaml
│
├── memory/                      # Persistent memory
│   ├── agent_definitions/
│   ├── execution_history/
│   ├── optimization_knowledge/
│   ├── workflow_templates/
│   ├── risk_scoring_history/
│   ├── event_triggers/
│   └── schemas/
│
├── monitoring/                 # Risk monitoring
│   └── risk_monitor.py
│
├── optimization/               # Agent optimization
│   └── agent_optimizer.py
│
├── validation/                  # Validation engine
│   ├── validation_engine.py
│   ├── rules/validation_rules.yaml
│   └── schemas/
│
├── workflows/                   # Workflow engine
│   ├── process_workflow.py
│   └── example_quant_research.json
│
├── telegram_watchtower/         # Telegram bot
│   ├── bot_controller.py
│   ├── command_processor.py
│   ├── bot_menu.py             # Inline keyboard menus
│   ├── event_monitor.py
│   ├── log_tailer.py
│   ├── config.yaml
│   ├── start_watchtower.sh
│   ├── install_service.sh
│   └── telegram-watchtower.service
│
├── paper_trading/               # Paper Trading Engine (7-layer architecture)
│   ├── engine.py               # Main PaperTradingEngine
│   ├── config.yaml             # Trading configuration
│   ├── run_paper_trading.py    # Launcher script
│   ├── telegram_commands.py    # Telegram bot commands
│   ├── dashboard/              # Web dashboard
│   │   ├── app.py
│   │   └── templates/index.html
│   └── layers/                 # 7-layer architecture
│       ├── layer1_data/        # Data & Connectivity
│       ├── layer2_risk/       # Risk Management
│       ├── layer3_signals/     # Signal Generation
│       ├── layer4_intelligence/ # Intelligence (ML/AI)
│       ├── layer5_execution/   # Execution
│       └── layer6_orchestration/ # Orchestration
│
├── vnpy_engine/                # VNPY Trading Engine
│   ├── tests/                  # Test suite (60 tests)
│   ├── cta_strategies.py       # CTA Strategies
│   ├── rl_module.py            # RL Module
│   └── test_validate.py        # Validation
│
├── data_lab/                    # Data Laboratory
│
├── logs/                        # Log files
│   ├── risk_monitor.log
│   ├── workflow_nohup.log
│   ├── optimizer_nohup.log
│   └── telegram_watchtower*.log
│
├── docs/                        # Documentation
│   ├── memory-system.md
│   ├── agent-configuration.md
│   ├── workflow-system.md
│   ├── telegram-bot.md
│   ├── risk-monitoring.md
│   └── validation-engine.md
│
├── stress_test.py               # Load testing
├── integration_test.py          # Integration tests
└── e2e_test.py                  # End-to-end tests
```

## Quick Start

### Prerequisites
- Python 3.8+
- pip
- Linux/Unix system (for systemd service)

### Installation

```bash
# 1. Clone or download the repository
cd financial_orchestrator

# 2. Run main setup
./setup.sh

# 3. Initialize agents
./setup_agents.sh

# 4. Configure Telegram bot
./setup_telegram_bot.sh
```

### Starting the System

#### Option 1: Master Startup Script (Recommended)

Start all components with a single command:

```bash
# Start everything
./start_system.sh

# Stop everything
./stop_system.sh
```

This starts:
- Telegram Bot (@NkhekheAlphaBot)
- Risk Monitor
- Validation Engine
- Agent Optimizer
- Workflow Processor

#### Option 2: Individual Components

```bash
# Telegram monitoring bot only
./telegram_watchtower/start_watchtower.sh

# Or use systemd (after installation)
sudo systemctl start telegram-watchtower
```

### Systemd Service (Production)

```bash
# Install the service
sudo cp financial-orchestrator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable financial-orchestrator

# Start the service
sudo systemctl start financial-orchestrator
```

## Autonomous Trading Bot

The autonomous trading bot is a self-learning, self-healing trading system with 75x leverage on Binance Futures.

### Key Features
- **Max 5 Trades/Day** - Risk-managed trading
- **Self-Learning** - Learns from trade outcomes
- **Adaptive Strategy** - Switches based on market regime
- **Continuous Reports** - 30-second Telegram updates
- **Daily Reports** - Comprehensive performance summaries

### Files
| File | Description |
|------|-------------|
| `autonomous_trading.py` | Main trading bot |
| `AUTONOMOUS_TRADING.md` | Full documentation |
| `docs/AUTONOMOUS_QUICKSTART.md` | Quick start guide |

### Quick Start
```bash
# Start trading bot
nohup ./venv/bin/python3 -u autonomous_trading.py > logs/autonomous_trading.log 2>&1 &

# Check status
ps aux | grep autonomous_trading
tail -f logs/autonomous_trading.log
```

### Telegram Commands
- `/trade` - Trading status
- `/balance` - Check balance
- `/positions` - Open positions
- `/long [qty]` - Open LONG
- `/short [qty]` - Open SHORT
- `/close` - Close position

## Configuration

### Agent Configuration
Edit YAML files in `agents/` directory:

```yaml
agent_id: "ai_engineer_001"
agent_name: "Quantitative AI Engineer"
role: "AI Engineer"
workload_capacity: 2
status: "available"
kill_switch_enabled: true
```

### Risk Thresholds
Configure in `configs/risk_scoring.yaml`:

```yaml
thresholds:
  low: 0.3
  medium: 0.6
  high: 0.8
```

### Telegram Bot
Edit `telegram_watchtower/config.yaml`:

```yaml
telegram:
  bot_token: "your_token_here"
  allowed_chat_ids:
    - your_chat_id
```

## Running Tests

```bash
# Stress test
python stress_test.py

# Integration test
python integration_test.py

# End-to-end test
python e2e_test.py
```

## Common Issues

### Bot not responding
1. Check bot token in config.yaml
2. Reset offset: `curl "https://api.telegram.org/bot<TOKEN>/getUpdates?offset=-1"`
3. Verify chat_id is in allowed_chat_ids

### Memory errors
- Reduce `max_log_buffer_mb` in config.yaml
- Increase cleanup interval

### Agent not responding
- Check kill_switch_enabled in config
- Review agent logs in logs/

## Documentation

See `docs/` directory for detailed component documentation:
- `memory-system.md` - Persistent memory structure
- `agent-configuration.md` - Agent setup guide
- `workflow-system.md` - Workflow creation and execution
- `telegram-bot.md` - Bot commands and service setup
- `risk-monitoring.md` - Risk configuration
- `validation-engine.md` - Validation rules
- `PAPER_TRADING.md` - Paper Trading Engine (7-layer architecture)
- `VNPY_ENGINE.md` - VNPY Trading Engine with RL integration
- `architecture-diagrams.md` - System architecture diagrams

## License

MIT License - see LICENSE file for details.
