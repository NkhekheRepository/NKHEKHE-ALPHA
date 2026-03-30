# Architecture Diagrams

## System Architecture (Mermaid)

```mermaid
flowchart TB
    subgraph Core["Core System"]
        WFE["Workflow Engine"]
        RM["Risk Monitor"]
        VE["Validation Engine"]
        AO["Agent Optimizer"]
    end
    
    subgraph Memory["Persistent Memory"]
        AD["Agent Definitions"]
        EH["Execution History"]
        OK["Optimization Knowledge"]
        WT["Workflow Templates"]
    end
    
    subgraph Agents["Multi-Agent System"]
        AE["AI Engineer"]
        DE["Data Engineer"]
        AP["API Tester"]
        FT["Finance Tracker"]
    end
    
    subgraph External["External Services"]
        TG["Telegram Bot<br/>@NkhekheAlphaBot"]
        API["External APIs"]
        LOGS["Log Files"]
    end
    
    WFE --> Memory
    RM --> Memory
    VE --> Memory
    AO --> Memory
    
    WFE --> Agents
    RM --> VE
    VE --> WFE
    
    TG --> LOGS
    TG --> WFE
    TG --> RM
    
    AE --> WFE
    DE --> WFE
    AP --> WFE
    FT --> WFE
```

## Data Flow

```mermaid
sequenceDiagram
    participant User
    participant TG as Telegram Bot
    participant WFE as Workflow Engine
    participant Agent as Agents
    participant MEM as Memory
    participant RM as Risk Monitor
    
    User->>TG: Send command
    TG->>WFE: Forward request
    WFE->>MEM: Load context
    WFE->>Agent: Assign task
    Agent->>Agent: Execute task
    Agent->>RM: Check risk
    RM->>MEM: Update risk history
    Agent->>MEM: Save results
    WFE->>TG: Return response
    TG->>User: Notify completion
```

## Directory Structure

```
financial_orchestrator/
├── agents/                    # Agent YAML configurations
│   ├── ai_engineer_config.yaml
│   ├── data_engineer_config.yaml
│   ├── api_tester_config.yaml
│   └── finance_tracker_config.yaml
├── memory/                    # Persistent memory storage
│   ├── agent_definitions/     # Agent configs in memory format
│   ├── execution_history/     # Session & execution logs
│   ├── optimization_knowledge/ # Learned optimizations
│   └── workflow_templates/    # Reusable workflow templates
├── workflows/                 # Workflow definitions
├── monitoring/                # Risk monitoring
├── optimization/              # Agent optimization
├── validation/                # Validation rules & schemas
├── telegram_watchtower/       # Telegram bot system
└── docs/                      # Documentation
```

## Telegram Watchtower Flow

```mermaid
flowchart LR
    subgraph Input
        CMDS["Commands"]
        ALERTS["Alerts"]
        LOGS["Log Files"]
    end
    
    subgraph Bot["Telegram Watchtower"]
        BT["Bot Controller"]
        CP["Command Processor"]
        EM["Event Monitor"]
        LT["Log Tailer"]
    end
    
    subgraph Output
        STATS["Stats"]
        NOTIF["Notifications"]
    end
    
    CMDS --> BT
    ALERTS --> EM
    LOGS --> LT
    BT --> CP
    EM --> NOTIF
    LT --> STATS
```

## VNPY Trading Engine Architecture

```mermaid
flowchart TB
    subgraph vnpy_engine["VNPY Trading Engine"]
        subgraph Strategies["CTA Strategies"]
            Momentum["MomentumCtaStrategy<br/>SMA Crossover"]
            MeanRev["MeanReversionCtaStrategy<br/>Bollinger Bands"]
            Breakout["BreakoutCtaStrategy<br/>Channel Breakout"]
            RLEnhanced["RlEnhancedCtaStrategy<br/>RL Validated"]
        end
        
        subgraph RL["RL Module"]
            MDP["TradingMDP<br/>Gym Environment"]
            PPO["PPO Agent<br/>Stable-Baselines3"]
        end
        
        subgraph Core["Core Components"]
            AM["ArrayManager<br/>Technical Analysis"]
            CTA["CtaTemplate<br/>Base Class"]
            Engine["CtaEngine<br/>Order Management"]
        end
        
        subgraph Tests["Testing (10 Tests)"]
            Pytest["pytest<br/>Integration Tests"]
            Fixtures["Fixtures<br/>Mock Engines"]
        end
    end
    
    RLEnhanced --> MDP
    RLEnhanced --> PPO
    Strategies --> AM
    AM --> CTA
    CTA --> Engine
    Pytest --> Fixtures
    Fixtures --> Strategies
```

### VNPY Strategy Data Flow

```mermaid
flowchart LR
    subgraph Input
        Bars["OHLCV Bars"]
    end
    
    subgraph Process
        AM["ArrayManager<br/>100 bars min"]
        Calc["Indicator<br/>SMA, ATR, BB"]
        Signal["Signal<br/>Crossover/Breakout"]
        RLVal["RL Validation<br/>Approve/Reject"]
    end
    
    subgraph Output
        Order["Order<br/>Buy/Sell/Short/Cover"]
        Trade["Trade<br/>Execution"]
    end
    
    Bars --> AM
    AM --> Calc
    Calc --> Signal
    Signal --> RLVal
    RLVal --> Order
    Order --> Trade
```

### Directory Structure - VNPY Engine

```
vnpy_engine/
├── vnpy_local/
│   ├── strategies/
│   │   └── cta_strategies.py     # 4 CTA strategies
│   ├── rl_module.py              # RL agent & MDP
│   ├── market_data.py            # Market data
│   ├── main_engine.py            # Main engine
│   ├── api_gateway.py            # Exchange API
│   ├── risk_manager.py           # Risk management
│   └── shared_state.py           # State management
├── tests/
│   ├── test_rl_cta_integration.py # 10 tests
│   ├── conftest.py               # Test fixtures
│   └── test_cta_strategies.py
├── config/
│   └── strategies.json
├── Dockerfile
└── docker-compose.yml
```

### Key Components

| Component | File | Purpose |
|-----------|------|---------|
| MomentumCtaStrategy | cta_strategies.py:16 | SMA crossover |
| MeanReversionCtaStrategy | cta_strategies.py:118 | Bollinger Bands |
| BreakoutCtaStrategy | cta_strategies.py:209 | Channel breakout |
| RlEnhancedCtaStrategy | cta_strategies.py:293 | RL-validated |
| TradingMDP | rl_module.py:36 | Gym environment |
| PPO Agent | rl_module.py:200 | Decision making |
| MockCtaEngine | conftest.py:185 | Testing |
| SyntheticDataGenerator | conftest.py:22 | Test data |
