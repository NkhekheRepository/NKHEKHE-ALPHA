# Agent Configuration Guide

The Financial Orchestrator uses a multi-agent architecture with four specialized agents, each configured via YAML files.

## Agent Types

| Agent | Config File | Specialization |
|-------|-------------|----------------|
| AI Engineer | `ai_engineer_config.yaml` | ML model development, Qlib |
| Data Engineer | `data_engineer_config.yaml` | Data ingestion, feature engineering |
| API Tester | `api_tester_config.yaml` | Endpoint validation, load testing |
| Finance Tracker | `finance_tracker_config.yaml` | Portfolio tracking, risk metrics |

## Agent Configuration Template

```yaml
# Basic Information
agent_id: "unique_agent_id"
agent_name: "Human Readable Name"
division: "Engineering" | "Operations" | "Finance"
role: "AI Engineer" | "Data Engineer" | "API Tester" | "Finance Tracker"

# Personality and Skills
personality_traits:
  - "trait1"
  - "trait2"
specializations:
  - "area1"
  - "area2"
financial_specializations:
  - "quantitative model development"
  - "factor discovery"

# Tools and Frameworks
tools:
  - "Qlib"
  - "TensorFlow"
  - "PyTorch"

# Responsibilities and Deliverables
responsibilities:
  - "Responsibility 1"
  - "Responsibility 2"
deliverables:
  - "Deliverable 1"
  - "Deliverable 2"

# Collaboration
communication_style: "technical and focused"
collaboration_patterns:
  - "Pattern 1"
  - "Pattern 2"

# Performance Metrics
performance_metrics:
  metric_name: "unit"  # e.g., "sharpe_ratio": "ratio"

# Workload Management
workload_capacity: 2        # Max concurrent tasks
current_workload: 0        # Current active tasks
last_active: ""            # ISO timestamp
status: "available"        # available | busy | offline

# Risk and Safety
risk_tolerance: "low" | "medium" | "high"
kill_switch_enabled: true   # Emergency stop
```

## Complete Example: AI Engineer

```yaml
agent_id: "ai_engineer_001"
agent_name: "Quantitative AI Engineer"
division: "Engineering"
role: "AI Engineer"

personality_traits:
  - "innovative"
  - "curious"
  - "rigorous"
  - "experimental"

specializations:
  - "machine learning"
  - "deep learning"
  - "feature engineering"
  - "model optimization"

financial_specializations:
  - "quantitative model development"
  - "factor discovery"
  - "time-series forecasting"
  - "reinforcement learning for trading"

tools:
  - "Qlib"
  - "TensorFlow"
  - "PyTorch"
  - "Scikit-learn"
  - "XGBoost"
  - "LightGBM"
  - "Optuna"
  - "Weights & Biases"

responsibilities:
  - "Develop and train quantitative models using Qlib"
  - "Perform feature engineering on financial data"
  - "Optimize model hyperparameters"
  - "Implement backtesting frameworks"
  - "Conduct model validation and testing"
  - "Deploy models for production use"

deliverables:
  - "Trained quantitative models"
  - "Feature importance reports"
  - "Backtesting results"
  - "Model performance metrics"
  - "Deployment-ready model artifacts"

communication_style: "technical and exploratory, focuses on model performance and innovation"

collaboration_patterns:
  - "Works closely with Data Engineers for clean data"
  - "Collaborates with Finance Trackers to validate outputs"
  - "Works with API Testers for model API reliability"
  - "Reports to Product Management on progress"

performance_metrics:
  model_accuracy: "percentage"
  sharpe_ratio: "ratio"
  max_drawdown: "percentage"
  information_ratio: "ratio"
  training_time: "minutes/hours"

workload_capacity: 2
current_workload: 0
last_active: ""
status: "available"

financial_data_sources:
  - "Processed data from Data Engineers"
  - "Qlib features"

risk_tolerance: "medium"
kill_switch_enabled: true
```

## Workload Management

Agents track their workload to prevent over-allocation:

```python
# Check if agent can accept new task
def can_accept_task(agent_config):
    return (agent_config['current_workload'] < 
            agent_config['workload_capacity'])

# Assign task to agent
def assign_task(agent_config, task):
    if can_accept_task(agent_config):
        agent_config['current_workload'] += 1
        agent_config['last_active'] = datetime.now().isoformat()
        return True
    return False

# Complete task
def complete_task(agent_config):
    agent_config['current_workload'] -= 1
    agent_config['last_active'] = datetime.now().isoformat()
```

## Kill Switch

Every agent has a kill switch for emergency stops:

```yaml
kill_switch_enabled: true  # Set to false to disable
```

```python
def execute_task(agent, task):
    if not agent.config.get('kill_switch_enabled', True):
        raise RuntimeError("Kill switch is disabled")
    
    # Execute task...
```

## Adding a New Agent

### Step 1: Create Configuration File
```bash
cp configs/agent_template.yaml agents/my_agent_config.yaml
```

### Step 2: Edit Configuration
```yaml
agent_id: "my_agent_001"
agent_name: "My Custom Agent"
role: "Custom"
# ... fill in details
```

### Step 3: Load to Memory
```bash
./setup_agents.sh
```

### Step 4: Verify
```bash
ls memory/agent_definitions/
# Should show my_agent_config.yaml
```

## Agent Communication Patterns

### Direct Collaboration
```yaml
collaboration_patterns:
  - "Works with Data Engineers for input data"
  - "Reports to Finance Trackers for validation"
```

### Task Routing
```python
def route_task(task_type):
    agents = {
        'model_development': 'ai_engineer',
        'data_processing': 'data_engineer',
        'endpoint_testing': 'api_tester',
        'risk_tracking': 'finance_tracker'
    }
    return agents.get(task_type, 'data_engineer')  # default
```

## Performance Tracking

Agents track their own performance metrics:

```json
{
  "agent_id": "ai_engineer_001",
  "metrics": {
    "tasks_completed": 42,
    "average_duration": 180.5,
    "success_rate": 0.95,
    "last_evaluation": "2026-03-29T15:00:00Z"
  }
}
```

## Troubleshooting

### Agent Not Responding
1. Check `status` in config (should be `available`)
2. Verify `kill_switch_enabled: true`
3. Check if `current_workload >= workload_capacity`
4. Review logs in `logs/`

### Agent Overloaded
1. Reduce workload: `current_workload` in YAML
2. Increase capacity: `workload_capacity` in YAML
3. Add more agent instances

### Task Routing Issues
1. Verify `agent_id` matches in workflow JSON
2. Check agent exists in `memory/agent_definitions/`
3. Review task routing logic in `workflows/process_workflow.py`
