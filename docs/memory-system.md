# Persistent Memory System

The Financial Orchestrator uses a file-based persistent memory system to store agent knowledge, execution history, and optimization data across sessions.

## Directory Structure

```
memory/
├── agent_definitions/        # Persisted agent configurations (YAML)
├── execution_history/         # Session logs and metrics (JSON)
├── optimization_knowledge/    # Agent learnings and performance (JSON)
├── workflow_templates/        # Reusable workflow definitions (YAML)
├── risk_scoring_history/      # Historical risk scores (JSON)
├── event_triggers/           # Automated event responses (JSON)
└── schemas/                  # JSON schema definitions (JSON)
```

## Storage Formats

### Agent Definitions (YAML)
Located: `memory/agent_definitions/`

Stores the full agent configuration for persistent access across sessions.

```yaml
# Example: ai_engineer.yaml
agent_id: "ai_engineer_001"
agent_name: "Quantitative AI Engineer"
division: "Engineering"
role: "AI Engineer"
personality_traits: ["innovative", "curious", "rigorous", "experimental"]
specializations: ["machine learning", "deep learning", "feature engineering"]
tools: ["Qlib", "TensorFlow", "PyTorch", "XGBoost"]
responsibilities:
  - "Develop quantitative models"
  - "Perform feature engineering"
  - "Optimize hyperparameters"
workload_capacity: 2
current_workload: 0
status: "available"
kill_switch_enabled: true
```

### Execution History (JSON)
Located: `memory/execution_history/`

Stores session logs with timestamp format `session_YYYYMMDD_HHMMSS.json`.

```json
{
  "execution_id": "exec_001",
  "orchestrator_id": "financial_orchestrator_001",
  "start_time": "2026-03-29T14:55:00Z",
  "end_time": null,
  "status": "running",
  "phases_completed": [
    {
      "phase": "Initial Setup",
      "tasks": ["Create project structure"],
      "duration_seconds": 120,
      "status": "completed",
      "success": true
    }
  ],
  "current_operations": [
    {
      "operation": "Risk monitoring",
      "status": "active",
      "risk_score": 0.25,
      "risk_level": "low"
    }
  ],
  "metrics": {
    "agents_deployed": 4,
    "workflows_managed": 1,
    "risk_alerts_triggered": 0
  },
  "knowledge_gained": [],
  "lessons_learned": [
    {
      "lesson": "Background processes require nohup",
      "context": "Scripts terminate when bash session ends",
      "resolution": "Use nohup and redirect output"
    }
  ],
  "next_steps": [],
  "last_updated": "2026-03-29T15:15:00Z"
}
```

### Optimization Knowledge (JSON)
Located: `memory/optimization_knowledge/`

Stores agent performance learnings with format `optimization_YYYYMMDD_HHMMSS.json`.

```json
{
  "timestamp": "2026-03-29T15:50:56.724830",
  "optimization": {
    "type": "agent_promotion",
    "agent_id": "agent_7",
    "reason": "High performance: 100.00% success, 1s avg duration",
    "suggestion": "Consider assigning more complex tasks"
  },
  "status": "applied",
  "notes": "Optimization recommendation processed"
}
```

### Workflow Templates (YAML)
Located: `memory/workflow_templates/`

Stores reusable workflow definitions.

```yaml
workflow_id: "quant_research_workflow"
workflow_name: "Quantitative Research Workflow"
description: "Standard workflow for equity factor model development"
phases:
  - name: "Data Acquisition"
    tasks:
      - id: "data_acq_001"
        name: "Market Data Ingestion"
        agent_type: "Data Engineer"
        estimated_duration: "30 minutes"
  - name: "Feature Engineering"
    tasks:
      - id: "feat_eng_001"
        name: "Technical Indicators"
        agent_type: "AI Engineer"
        estimated_duration: "60 minutes"
risk_tolerance: "medium"
```

## How Memory is Used

### 1. Agent Initialization
When the system starts, agents load their definitions from `memory/agent_definitions/`:

```python
def load_agent_definitions():
    agent_dir = "memory/agent_definitions/"
    for filename in os.listdir(agent_dir):
        if filename.endswith('.yaml'):
            with open(os.path.join(agent_dir, filename)) as f:
                yield yaml.safe_load(f)
```

### 2. Execution Tracking
Each workflow execution creates a session file in `execution_history/`:

```python
def start_execution_session():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_file = f"memory/execution_history/session_{timestamp}.json"
    # ... create session file with initial state
```

### 3. Knowledge Accumulation
The optimizer stores learnings for future reference:

```python
def store_optimization(optimization_data):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"memory/optimization_knowledge/optimization_{timestamp}.json"
    with open(file_path, 'w') as f:
        json.dump(optimization_data, f, indent=2)
```

## Managing Memory

### Adding a New Agent Definition
```bash
# Create a new YAML file in memory/agent_definitions/
cp configs/agent_template.yaml memory/agent_definitions/my_agent.yaml
# Edit with your agent configuration
```

### Viewing Execution History
```bash
# List all sessions
ls -la memory/execution_history/

# View latest session
cat memory/execution_history/session_*.json | tail -1
```

### Clearing Old Data
```bash
# Remove sessions older than 30 days
find memory/execution_history/ -name "session_*.json" -mtime +30 -delete

# Remove old optimization records
find memory/optimization_knowledge/ -name "optimization_*.json" -mtime +90 -delete
```

## Backup and Restore

### Backup
```bash
# Backup entire memory directory
tar -czf memory_backup_$(date +%Y%m%d).tar.gz memory/
```

### Restore
```bash
# Restore from backup
tar -xzf memory_backup_20260329.tar.gz
```

## Best Practices

1. **Regular Backups**: Backup memory before major changes
2. **Clean Old Sessions**: Remove sessions older than 30-90 days
3. **Validate YAML**: Ensure agent definitions are valid YAML
4. **Monitor Disk Usage**: Memory files can grow over time
5. **Gitignore Sensitive Data**: Don't commit execution_history/ if contains sensitive info
