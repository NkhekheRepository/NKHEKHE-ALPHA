# Workflow System

The Financial Orchestrator uses a phase-based workflow engine for executing complex multi-step processes like quantitative research.

## Workflow Structure

```
Workflow
├── Metadata (id, name, status)
├── Phases[]
│   ├── Phase Name
│   ├── Status (pending, in_progress, completed, failed)
│   └── Tasks[]
│       ├── Task ID
│       ├── Name
│       ├── Description
│       ├── Agent Type
│       ├── Assigned Agent
│       ├── Status
│       ├── Validation Results
│       └── Deliverables
└── Risk Score
```

## Workflow JSON Schema

```json
{
  "workflow_id": "unique_workflow_id",
  "workflow_name": "Human Readable Name",
  "description": "What this workflow does",
  "start_time": "ISO timestamp",
  "end_time": null,
  "status": "pending | running | completed | failed | paused",
  "current_phase": "Phase Name",
  "progress_percentage": 0-100,
  "phases": [
    {
      "name": "Phase Name",
      "status": "pending | in_progress | completed | failed",
      "tasks": [
        {
          "id": "task_id_001",
          "name": "Task Name",
          "description": "Task description",
          "agent_type": "AI Engineer | Data Engineer | API Tester | Finance Tracker",
          "assigned_agent": "agent_id from config",
          "status": "pending | in_progress | completed | failed | skipped",
          "start_time": null,
          "estimated_duration": "30 minutes",
          "progress_percentage": 0,
          "deliverables": ["Deliverable 1"],
          "validation_results": {}
        }
      ]
    }
  ],
  "risk_score": 0.0,
  "risk_level": "low | medium | high | critical",
  "notes": "Additional notes",
  "last_updated": "ISO timestamp"
}
```

## Example: Quantitative Research Workflow

```json
{
  "workflow_id": "quant_research_001",
  "workflow_name": "Example Quant Research Workflow",
  "description": "Demonstration workflow for equity factor model development",
  "start_time": "2026-03-29T15:00:00Z",
  "status": "running",
  "current_phase": "Data Acquisition",
  "progress_percentage": 25,
  "phases": [
    {
      "name": "Data Acquisition",
      "status": "in_progress",
      "tasks": [
        {
          "id": "data_acq_001",
          "name": "Market Data Ingestion",
          "description": "Ingest price, volume, and fundamental data",
          "agent_type": "Data Engineer",
          "assigned_agent": "data_engineer_001",
          "status": "completed",
          "start_time": "2026-03-29T15:00:00Z",
          "estimated_duration": "30 minutes",
          "progress_percentage": 100,
          "deliverables": ["Raw market data in standardized format"],
          "validation_results": {
            "data_completeness": "passed",
            "timestamp_consistency": "passed",
            "price_volume_validity": "passed"
          }
        },
        {
          "id": "data_acq_002",
          "name": "Alternative Data Integration",
          "description": "Ingest alternative data (news, sentiment)",
          "agent_type": "Data Engineer",
          "assigned_agent": "data_engineer_001",
          "status": "pending",
          "start_time": null,
          "estimated_duration": "45 minutes",
          "progress_percentage": 0
        }
      ]
    },
    {
      "name": "Feature Engineering",
      "status": "pending",
      "tasks": [
        {
          "id": "feat_eng_001",
          "name": "Technical Indicator Calculation",
          "description": "Calculate moving averages, RSI, MACD",
          "agent_type": "AI Engineer",
          "assigned_agent": "ai_engineer_001",
          "status": "pending",
          "start_time": null,
          "estimated_duration": "60 minutes"
        }
      ]
    }
  ],
  "risk_score": 0.15,
  "risk_level": "low"
}
```

## Workflow Phases

### Standard Phase Sequence

1. **Data Acquisition** - Ingest market and alternative data
2. **Data Processing** - Clean and normalize data
3. **Feature Engineering** - Create trading signals
4. **Model Development** - Train and validate models
5. **Backtesting** - Test strategy on historical data
6. **Optimization** - Tune parameters
7. **Deployment** - Deploy to production

## Creating a Custom Workflow

### Step 1: Create Workflow File

Create a JSON file in `workflows/` or `memory/workflow_templates/`:

```bash
cat > workflows/my_workflow.json << 'EOF'
{
  "workflow_id": "custom_workflow_001",
  "workflow_name": "My Custom Workflow",
  "description": "Description of what this workflow does",
  "start_time": null,
  "status": "pending",
  "current_phase": null,
  "progress_percentage": 0,
  "phases": [
    {
      "name": "Phase 1",
      "status": "pending",
      "tasks": []
    }
  ],
  "risk_score": 0.0,
  "risk_level": "low",
  "notes": "",
  "last_updated": null
}
EOF
```

### Step 2: Add Tasks

Edit the workflow JSON and add tasks:

```json
{
  "phases": [
    {
      "name": "Data Acquisition",
      "status": "pending",
      "tasks": [
        {
          "id": "my_task_001",
          "name": "My Task",
          "description": "What this task does",
          "agent_type": "Data Engineer",
          "assigned_agent": null,
          "status": "pending",
          "start_time": null,
          "estimated_duration": "30 minutes",
          "progress_percentage": 0,
          "deliverables": [],
          "validation_results": {}
        }
      ]
    }
  ]
}
```

### Step 3: Execute Workflow

```python
from workflows.process_workflow import WorkflowEngine

engine = WorkflowEngine()
workflow = engine.load_workflow("workflows/my_workflow.json")
engine.execute_workflow(workflow)
```

## Workflow Engine API

### Load Workflow
```python
def load_workflow(self, path: str) -> dict:
    """Load workflow from JSON file"""
    with open(path) as f:
        return json.load(f)
```

### Execute Workflow
```python
def execute_workflow(self, workflow: dict) -> dict:
    """Execute a workflow from start to finish"""
    workflow['status'] = 'running'
    workflow['start_time'] = datetime.now().isoformat()
    
    for phase in workflow['phases']:
        self.execute_phase(phase)
    
    workflow['status'] = 'completed'
    return workflow
```

### Execute Phase
```python
def execute_phase(self, phase: dict) -> None:
    """Execute all tasks in a phase"""
    phase['status'] = 'in_progress'
    
    for task in phase['tasks']:
        self.execute_task(task)
    
    phase['status'] = 'completed'
```

### Execute Task
```python
def execute_task(self, task: dict, agent: str) -> None:
    """Execute a single task with assigned agent"""
    task['status'] = 'in_progress'
    task['start_time'] = datetime.now().isoformat()
    
    # Route to appropriate agent
    agent_instance = self.get_agent(task['agent_type'])
    
    # Execute
    result = agent_instance.execute(task)
    
    task['status'] = 'completed'
    task['progress_percentage'] = 100
```

## Workflow State Persistence

Workflows persist their state to JSON files:

```python
def save_workflow_state(workflow: dict):
    """Save workflow state to file"""
    path = f"workflows/{workflow['workflow_id']}_state.json"
    with open(path, 'w') as f:
        json.dump(workflow, f, indent=2)
```

## Progress Tracking

### Calculate Progress
```python
def calculate_progress(workflow: dict) -> int:
    """Calculate overall workflow progress percentage"""
    total_tasks = 0
    completed_tasks = 0
    
    for phase in workflow['phases']:
        for task in phase['tasks']:
            if task['status'] != 'skipped':
                total_tasks += 1
            if task['status'] == 'completed':
                completed_tasks += 1
    
    return int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
```

### Update Risk Score
```python
def update_risk_score(workflow: dict) -> tuple:
    """Update workflow risk score based on tasks"""
    # Risk calculation logic
    risk_score = calculate_risk(workflow)
    risk_level = "low" if risk_score < 0.3 else "medium"
    
    workflow['risk_score'] = risk_score
    workflow['risk_level'] = risk_level
    
    return risk_score, risk_level
```

## Workflow Templates

Templates are stored in `memory/workflow_templates/` for reuse:

```yaml
# Example template: quant_research_workflow.yaml
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

## Troubleshooting

### Workflow Stuck in "in_progress"
1. Check agent availability
2. Verify task has `assigned_agent`
3. Review logs for agent errors

### Tasks Not Routing Correctly
1. Verify `agent_type` matches available agents
2. Check agent definitions in `memory/agent_definitions/`

### Workflow Validation Failures
1. Check task `validation_results` in workflow JSON
2. Review `validation_rules.yaml` thresholds
3. Ensure data deliverables match requirements
