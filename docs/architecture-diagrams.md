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
