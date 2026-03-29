# Risk Monitoring System

The Financial Orchestrator includes a comprehensive risk monitoring system that tracks, analyzes, and alerts on potential risks in real-time.

## Risk Levels

| Level | Score Range | Color | Action |
|-------|-------------|-------|--------|
| **Low** | 0.0 - 0.3 | Green | Normal operations |
| **Medium** | 0.3 - 0.6 | Yellow | Enhanced monitoring |
| **High** | 0.6 - 0.8 | Orange | Immediate attention |
| **Critical** | 0.8 - 1.0 | Red | Emergency response |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RISK MONITOR                             │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Risk Calculator                         │   │
│  │  • Market risk score                                 │   │
│  │  • Operational risk score                            │   │
│  │  • Combined risk score                              │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│    ┌──────────────────────┼──────────────────────┐         │
│    ▼                      ▼                      ▼         │
│  ┌────────┐          ┌──────────┐          ┌──────────┐     │
│  │Market  │          │Operational│          │  VaR     │     │
│  │Factors │          │ Factors  │          │ Monitor  │     │
│  └────────┘          └──────────┘          └──────────┘     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Alert System                             │   │
│  │  • Threshold alerts  • Proactive notifications       │   │
│  │  • Telegram alerts  • Log alerts                     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

Edit `configs/risk_scoring.yaml`:

```yaml
# Risk Scoring Configuration
scoring:
  market_risk_weight: 0.4
  operational_risk_weight: 0.3
  var_risk_weight: 0.3

# Risk Level Thresholds
thresholds:
  low: 0.3
  medium: 0.6
  high: 0.8
  critical: 0.9

# Alert Configuration
alerts:
  enabled: true
  telegram_notify: true
  log_alerts: true
  min_interval_seconds: 60  # Minimum time between same alerts

# VaR (Value at Risk) Settings
var:
  confidence_level: 0.95
  window_days: 252  # Trading days in a year
  max_var_percent: 0.05  # 5% max daily VaR

# Drawdown Settings
drawdown:
  max_drawdown_percent: 0.20  # 20% max drawdown
  warning_threshold: 0.15     # 15% warning threshold
```

## Risk Factors

### Market Risk Factors
- Portfolio volatility
- Beta exposure
- Sector concentration
- Factor exposures
- Correlation with market

### Operational Risk Factors
- Agent failures
- Workflow interruptions
- Data quality issues
- Validation failures
- System downtime

### VaR Monitoring
- Daily VaR calculation
- Historical simulation
- Parametric VaR
- Monte Carlo VaR

## Risk Score Calculation

```python
def calculate_risk_score(
    market_risk: float,
    operational_risk: float,
    var_risk: float
) -> tuple:
    """Calculate combined risk score"""
    
    weights = {
        'market': 0.4,
        'operational': 0.3,
        'var': 0.3
    }
    
    # Weighted average
    score = (
        market_risk * weights['market'] +
        operational_risk * weights['operational'] +
        var_risk * weights['var']
    )
    
    # Determine level
    if score < 0.3:
        level = "low"
    elif score < 0.6:
        level = "medium"
    elif score < 0.8:
        level = "high"
    else:
        level = "critical"
    
    return score, level
```

## Risk Monitor API

### Initialize Monitor
```python
from monitoring.risk_monitor import RiskMonitor, RiskLevel

monitor = RiskMonitor()
```

### Check Risk
```python
risk_score, risk_level = monitor.check_risk(
    market_data=market_data,
    portfolio_positions=positions
)
```

### Get Risk Status
```python
status = monitor.get_risk_status()
# Returns:
# {
#     'risk_score': 0.25,
#     'risk_level': 'low',
#     'market_risk': 0.2,
#     'operational_risk': 0.15,
#     'var_risk': 0.1,
#     'last_update': '2026-03-29T15:00:00Z'
# }
```

### Update Thresholds
```python
monitor.update_thresholds({
    'low': 0.25,
    'medium': 0.5,
    'high': 0.75,
    'critical': 0.9
})
```

## Risk Alerts

### Alert Types

| Type | Trigger | Action |
|------|---------|--------|
| **Threshold Breach** | Score exceeds threshold | Notify via Telegram |
| **VaR Breach** | VaR exceeds limit | Alert + Log |
| **Drawdown Alert** | Drawdown exceeds warning | Notify + Log |
| **Agent Failure** | Agent goes offline | Alert + Log |

### Alert Configuration
```yaml
alerts:
  risk_threshold:
    enabled: true
    levels:
      - level: "high"
        threshold: 0.6
        action: "notify"
      - level: "critical"
        threshold: 0.8
        action: "alert_all"
```

## Risk Scoring History

Risk scores are persisted to `memory/risk_scoring_history/`:

```json
{
  "timestamp": "2026-03-29T15:00:00Z",
  "risk_score": 0.25,
  "risk_level": "low",
  "components": {
    "market_risk": 0.2,
    "operational_risk": 0.15,
    "var_risk": 0.1
  },
  "factors": {
    "portfolio_volatility": 0.18,
    "beta_exposure": 0.22,
    "agent_health": 0.95
  }
}
```

## Real-time Monitoring

The risk monitor runs continuously:

```python
def start_monitoring():
    """Start continuous risk monitoring"""
    monitor = RiskMonitor()
    
    while True:
        # Calculate risk
        score, level = monitor.check_risk()
        
        # Check thresholds
        if level in ['high', 'critical']:
            monitor.send_alert(score, level)
        
        # Log risk
        monitor.log_risk(score, level)
        
        # Wait before next check
        time.sleep(60)  # Check every minute
```

## Integration with Telegram Bot

The risk monitor sends alerts to the Telegram bot:

```python
def send_alert(risk_score: float, risk_level: str):
    """Send risk alert to Telegram"""
    message = f"""
🚨 Risk Alert!

Level: {risk_level.upper()}
Score: {risk_score:.2%}

Action Required: {
    'low': 'Continue monitoring',
    'medium': 'Review positions',
    'high': 'Immediate attention needed',
    'critical': 'Emergency response required'
}[risk_level]
"""
    telegram_bot.send_message(message)
```

## Risk Limits

### Position Limits
```yaml
business_logic:
  position_limits:
    max_position_size: 0.1      # Max 10% in single position
    max_sector_exposure: 0.3    # Max 30% in single sector
```

### Risk Limits
```yaml
risk_limits:
  max_daily_var: 0.05          # Max 5% daily VaR
  max_drawdown: 0.20           # Max 20% drawdown
  max_leverage: 2.0            # Max 2x leverage
```

## Troubleshooting

### Risk Score Too High
1. Check market conditions
2. Verify data feeds
3. Review position sizes
4. Check agent health

### Alerts Not Sending
1. Verify Telegram bot is running
2. Check bot token in config
3. Verify chat_id is authorized
4. Check network connectivity

### Risk History Not Saving
1. Check write permissions on memory directory
2. Verify disk space
3. Check logs for errors

## Best Practices

1. **Set Appropriate Thresholds**: Calibrate based on risk tolerance
2. **Monitor Alert Fatigue**: Don't set thresholds too low
3. **Review Risk History**: Regular analysis of risk patterns
4. **Test Alert System**: Periodically test notifications
5. **Update Weights**: Adjust weights based on performance
