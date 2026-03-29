# Validation Engine

The Financial Orchestrator includes a comprehensive validation system for ensuring data quality, schema compliance, and business logic rules.

## Validation Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| **Basic** | Essential checks only | Quick validation |
| **Standard** | Common validation rules | Normal operations |
| **Strict** | Comprehensive validation | Production systems |
| **Paranoid** | Maximum scrutiny | High-risk decisions |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  VALIDATION ENGINE                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Validation Rules (validation_rules.yaml)     │   │
│  │  • Schema validation  • Data quality  • Business rules│   │
│  │  • Model validation  • Statistical tests             │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│    ┌──────────────────────┼──────────────────────┐         │
│    ▼                      ▼                      ▼         │
│  ┌────────┐          ┌──────────┐          ┌──────────┐     │
│  │Schema  │          │  Data    │          │ Business │     │
│  │Validate│          │ Quality  │          │  Logic   │     │
│  └────────┘          └──────────┘          └──────────┘     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Validation Reports                      │   │
│  │  • JSON reports  • HTML reports  • Trend analysis   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

Edit `validation/rules/validation_rules.yaml`:

```yaml
validation_enabled: true
validation_level: "strict"  # basic, standard, strict, paranoid

# Schema Validation
schema_validation:
  market_data:
    enabled: true
    schema_file: "../schemas/market_data_schema.json"
    required_for: ["data_acq_001", "data_acq_002"]
    error_threshold: 0.01  # Max 1% can fail
    
  model_output:
    enabled: true
    schema_file: "../schemas/model_output_schema.json"
    required_for: ["model_dev_002"]
    error_threshold: 0.0  # No errors allowed

# Data Quality Rules
data_quality:
  completeness:
    enabled: true
    min_completeness: 0.95  # 95% of data must be present
    checks:
      - "missing_values_check"
      - "expected_count_check"
      
  consistency:
    enabled: true
    max_inconsistency: 0.02
    checks:
      - "price_logic_check"  # high >= low
      - "timestamp_order_check"
      - "volume_non_negative"
      
  validity:
    enabled: true
    checks:
      - "extreme_value_check"
      - "return_reasonableness"
      - "volume_spike_detection"
```

## Validation Rules

### Schema Validation

Validates JSON data against JSON schemas:

```json
// schemas/market_data_schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["symbol", "timestamp", "open", "high", "low", "close", "volume"],
  "properties": {
    "symbol": {
      "type": "string",
      "pattern": "^[A-Z]{1,5}$"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "open": {"type": "number", "minimum": 0},
    "high": {"type": "number", "minimum": 0},
    "low": {"type": "number", "minimum": 0},
    "close": {"type": "number", "minimum": 0},
    "volume": {"type": "integer", "minimum": 0}
  }
}
```

### Data Quality Checks

```python
# Completeness Check
def check_completeness(data: dict, min_required: float = 0.95) -> bool:
    """Ensure data meets completeness threshold"""
    total_fields = len(data)
    non_null_fields = sum(1 for v in data.values() if v is not None)
    return (non_null_fields / total_fields) >= min_required

# Consistency Check
def check_price_consistency(data: dict) -> bool:
    """Ensure OHLC prices are logically consistent"""
    return (data['high'] >= data['low'] and
            data['high'] >= data['open'] and
            data['high'] >= data['close'] and
            data['low'] <= data['open'] and
            data['low'] <= data['close'])

# Validity Check
def check_extreme_values(data: dict, max_factor: float = 10.0) -> bool:
    """Check for extreme values"""
    median = (data['high'] + data['low']) / 2
    for price in [data['open'], data['close']]:
        if price > median * max_factor or price < median / max_factor:
            return False
    return True
```

### Business Logic Rules

```yaml
business_logic:
  position_limits:
    enabled: true
    max_position_size: 0.1      # Max 10% portfolio
    max_sector_exposure: 0.3    # Max 30% sector
    
  risk_limits:
    enabled: true
    max_daily_var: 0.05        # Max 5% daily VaR
    max_drawdown: 0.20         # Max 20% drawdown
    max_leverage: 2.0         # Max 2x leverage
```

## Validation Engine API

### Initialize Engine
```python
from validation.validation_engine import ValidationEngine

engine = ValidationEngine()
```

### Validate Data
```python
result = engine.validate(
    data=market_data,
    validation_type='market_data',
    level='strict'
)

# result = {
#     'valid': True/False,
#     'errors': [],
#     'warnings': [],
#     'metrics': {}
# }
```

### Validate Workflow Task
```python
result = engine.validate_task(task_output, task_id)
```

### Generate Report
```python
report = engine.generate_report(
    format='json'  # or 'html'
)
```

## Validation Workflow

```python
def validate_workflow_task(task: dict, workflow_id: str) -> dict:
    """Validate a single workflow task output"""
    
    # Load validation rules
    rules = load_validation_rules()
    
    # Get task-specific rules
    task_rules = get_task_rules(rules, task['id'])
    
    # Initialize results
    results = {
        'task_id': task['id'],
        'valid': True,
        'errors': [],
        'warnings': [],
        'metrics': {}
    }
    
    # Schema validation
    if task_rules.get('schema_validation'):
        schema_result = validate_schema(
            task['output'],
            task_rules['schema_file']
        )
        results['valid'] &= schema_result['valid']
        results['errors'].extend(schema_result['errors'])
    
    # Data quality validation
    if task_rules.get('data_quality'):
        quality_result = validate_quality(
            task['output'],
            task_rules['quality_checks']
        )
        results['valid'] &= quality_result['valid']
        results['warnings'].extend(quality_result['warnings'])
    
    # Check error threshold
    error_rate = len(results['errors']) / task_rules.get('error_threshold', 1)
    if error_rate > task_rules.get('error_threshold', 0.01):
        results['valid'] = False
        results['errors'].append('Error threshold exceeded')
    
    return results
```

## Escalation Rules

```yaml
alerting:
  validation_failures:
    enabled: true
    threshold: 3  # Alert after 3 consecutive failures
    escalation:
      - level: "agent"
        action: "log_and_notify"
        timeout: "5 minutes"
      - level: "supervisor"
        action: "pause_workflow"
        timeout: "15 minutes"
      - level: "management"
        action: "require_manual_approval"
        timeout: "1 hour"
```

## Validation Reports

Reports are saved to `validation/reports/`:

```json
{
  "report_id": "validation_20260329_150000",
  "timestamp": "2026-03-29T15:00:00Z",
  "validation_level": "strict",
  "summary": {
    "total_validations": 42,
    "passed": 40,
    "failed": 2,
    "pass_rate": 0.952
  },
  "failed_validations": [
    {
      "task_id": "data_acq_002",
      "validation_type": "schema",
      "errors": ["Missing required field: volume"]
    }
  ],
  "trends": {
    "pass_rate_trend": "stable",
    "common_failures": ["extreme_value_check"]
  }
}
```

## Model Validation Rules

```yaml
model_validation:
  statistical_significance:
    enabled: true
    min_p_value: 0.05
    metrics:
      - "information_ratio"
      - "sharpe_ratio"
      - "t_stat"
      
  overfitting_checks:
    enabled: true
    metrics:
      - "in_vs_out_sample_ratio"  # Should be > 0.5
      - "cross_validation_stability"
      - "parameter_stability"
```

## Performance Monitoring

Track validation performance over time:

```python
def track_validation_performance():
    """Track validation metrics over time"""
    return {
        'avg_validation_time': 0.5,  # seconds
        'pass_rate': 0.95,
        'common_failures': [],
        'last_10_validations': []
    }
```

## Troubleshooting

### Validation Taking Too Long
1. Reduce validation level (strict → standard)
2. Enable sampling for large datasets
3. Cache schema validations

### Too Many False Positives
1. Adjust error thresholds
2. Review validation rules
3. Check data source quality

### Reports Not Generating
1. Check write permissions on validation/reports/
2. Verify disk space
3. Check logs for errors

## Best Practices

1. **Start with Basic**: Begin with basic validation, add strict rules gradually
2. **Set Realistic Thresholds**: Balance between strictness and practicality
3. **Monitor Pass Rates**: Track validation metrics over time
4. **Document Custom Rules**: Add comments for complex business logic
5. **Regular Rule Reviews**: Periodically review and update validation rules
