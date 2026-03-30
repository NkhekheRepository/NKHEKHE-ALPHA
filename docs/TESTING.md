# Testing Guide

## Overview

This guide covers testing for the VNPY Trading Engine, including integration tests, test fixtures, and debugging procedures.

**Test Framework:** pytest  
**Test Location:** `vnpy_engine/tests/`  
**Test File:** `test_rl_cta_integration.py`  
**Test Results:** 10 tests passing

---

## Prerequisites

### Virtual Environment

```bash
cd /home/ubuntu/financial_orchestrator

# Create virtual environment (if not exists)
python3 -m venv venv

# Activate
source venv/bin/activate

# Verify Python
python --version
# Output: Python 3.12.x
```

### Dependencies

Required packages (installed via requirements.txt):

```
vnpy>=4.0.0
vnpy_ctastrategy>=1.4.0
stable-baselines3>=2.0.0
gymnasium>=0.29.0
numpy>=1.21.0
pytest>=7.0.0
```

### Verify Installation

```bash
python -c "import vnpy; print('VNPY:', vnpy.__version__)"
python -c "import pytest; print('pytest:', pytest.__version__)"
```

---

## Running Tests

### All Integration Tests

```bash
cd vnpy_engine
pytest tests/test_rl_cta_integration.py -v
```

### Specific Test Class

```bash
# Test RL-enhanced CTA integration
pytest tests/test_rl_cta_integration.py::TestRlEnhancedCTAIntegration -v

# Test performance comparison
pytest tests/test_rl_cta_integration.py::TestRLCTAPerformance -v

# Test end-to-end
pytest tests/test_rl_cta_integration.py::TestEndToEnd -v
```

### Single Test

```bash
pytest tests/test_rl_cta_integration.py::TestRlEnhancedCTAIntegration::test_rl_agent_loads -v
```

### With Output Capture

```bash
# Show print statements and logs
pytest tests/test_rl_cta_integration.py -v -s

# Show only failed tests
pytest tests/test_rl_cta_integration.py -v --tb=short
```

### With Coverage

```bash
pytest tests/test_rl_cta_integration.py -v --cov=vnpy_local --cov-report=term-missing
```

### Test Discovery

```bash
# List all tests without running
pytest tests/test_rl_cta_integration.py --collect-only
```

---

## Test Structure

### Test Classes

| Class | Tests | Purpose |
|-------|-------|---------|
| `TestRlEnhancedCTAIntegration` | 6 | Core RL-CTA functionality |
| `TestRLCTAPerformance` | 2 | Performance comparison |
| `TestEndToEnd` | 2 | End-to-end scenarios |

### Test List (10 Tests)

```python
class TestRlEnhancedCTAIntegration:
    def test_rl_agent_loads(self):
        """Test RL agent loads on strategy initialization."""
        
    def test_cta_signal_validated_by_rl(self):
        """Test CTA signals are validated by RL agent."""
        
    def test_rl_filter_approves_valid_signals(self):
        """Test RL approves valid CTA signals."""
        
    def test_rl_filter_rejects_invalid_signals(self):
        """Test RL rejects invalid CTA signals."""
        
    def test_fallback_when_rl_disabled(self):
        """Test strategy works when RL is disabled."""
        
    def test_fallback_on_rl_error(self):
        """Test strategy falls back when RL agent errors."""


class TestRLCTAPerformance:
    def test_rl_reduces_whipsaws(self):
        """Test RL filter reduces false signals."""
        
    def test_rl_preserves_trend_following(self):
        """Test RL doesn't filter out good signals."""


class TestEndToEnd:
    def test_full_trading_cycle(self):
        """Test complete trading cycle."""
        
    def test_multiple_strategies_compare(self):
        """Test comparing multiple strategies."""
```

---

## Test Fixtures (conftest.py)

### SyntheticDataGenerator

Generates synthetic OHLCV bar data for testing.

```python
from conftest import SyntheticDataGenerator

# Initialize
gen = SyntheticDataGenerator(symbol="BTCUSDT", initial_price=50000)
```

#### Methods

| Method | Description |
|--------|-------------|
| `generate_trending_bars(n, trend)` | Generate bars with clear trend ("up", "down", "sideways") |
| `generate_ranging_bars(n, center, width)` | Generate oscillating bars around center |
| `generate_volatile_bars(n, volatility)` | Generate high volatility bars |
| `generate_flash_crash(n_before, crash_pct)` | Generate bars with flash crash |

#### Usage Examples

```python
# Trending upward
bars = gen.generate_trending_bars(n=200, trend="up")

# Trending downward
bars = gen.generate_trending_bars(n=200, trend="down")

# Ranging market
bars = gen.generate_ranging_bars(n=100, center=50000, width=0.02)

# High volatility
bars = gen.generate_volatile_bars(n=100, volatility=0.03)

# Flash crash scenario
bars = gen.generate_flash_crash(n_before=50, crash_pct=0.10)
```

---

### MockCtaEngine

Mock CTA engine for strategy testing.

```python
from conftest import MockCtaEngine

engine = MockCtaEngine()
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `strategies` | dict | Registered strategies |
| `orders` | list | Order records |
| `trades` | list | Trade records |
| `positions` | dict | Position tracking |
| `logs` | list | Log messages |

#### Methods

| Method | Description |
|--------|-------------|
| `register_strategy(strategy)` | Register a strategy |
| `send_order(...)` | Mock order execution |
| `start_strategy(strategy)` | Start strategy (sets trading=True) |
| `get_position(vt_symbol, direction)` | Get current position |

#### Usage Example

```python
# Create mock engine
mock_cta_engine = MockCtaEngine()

# Create strategy
strategy = RlEnhancedCtaStrategy(
    cta_engine=mock_cta_engine,
    strategy_name="TestRL",
    vt_symbol="BTCUSDT.BINANCE",
    setting={"fast_window": 10, "slow_window": 30, "fixed_size": 1}
)

# Initialize (required!)
strategy.on_init()
strategy.trading = True  # Required for order execution!

# Process bars
for bar in bars:
    strategy.on_bar(bar)

# Check results
print(f"Trades: {len(mock_cta_engine.trades)}")
print(f"Logs: {mock_cta_engine.logs}")
```

---

### MockRLAgent

Mock RL agent for testing.

```python
from unittest.mock import Mock

mock_rl_agent = Mock()
```

#### Setup

```python
# Basic setup
mock_rl_agent.get_action.return_value = {
    "action": "buy",
    "action_idx": 1,
    "evaluation": {
        "expected_pnl": 100,
        "risk_metrics": {"var_95": -0.01}
    }
}

# With risk assessment
mock_rl_agent.get_action_with_risk.return_value = {
    "action": "hold",  # "hold", "buy", "sell", "close"
    "action_idx": 0,
    "evaluation": {"expected_pnl": -50, "risk_metrics": {}},
    "market_state": {},
    "timestamp": 0
}
```

#### Action Values

| action | action_idx | Meaning |
|--------|------------|---------|
| "hold" | 0 | Reject signal |
| "buy" | 1 | Approve long signal |
| "sell" | 2 | Approve short signal |
| "close" | 3 | Close position |

---

## Test Fixes Applied

### Problem 1: No Trades Executing

**Symptoms:** Tests run but no orders are placed.

**Root Cause:** CtaTemplate requires `trading = True` for order execution. The base class checks this flag before executing any orders.

**Original Code (Broken):**
```python
strategy = RlEnhancedCtaStrategy(...)
strategy.on_init()
# Missing: strategy.trading = True
# Orders blocked by CtaTemplate!
```

**Fixed Code:**
```python
strategy = RlEnhancedCtaStrategy(...)
strategy.on_init()
strategy.trading = True  # Required!
```

**Location Applied:** All 10 tests in `test_rl_cta_integration.py`

---

### Problem 2: ArrayManager Not Inited

**Symptoms:** `assert am.inited` fails or signals never generated.

**Root Cause:** ArrayManager needs 100 bars before `inited = True`. Tests using fewer bars would not trigger strategy logic.

**Original Code (Broken):**
```python
bars = gen.generate_trending_bars(n=50, trend="up")  # Only 50 bars
for bar in bars:
    strategy.on_bar(bar)
# am.inited still False!
```

**Fixed Code:**
```python
bars = gen.generate_trending_bars(n=200, trend="up")  # 200 bars
for bar in bars:
    strategy.on_bar(bar)
# am.inited = True after 100 bars
```

**Location Applied:** Multiple tests with increased bar counts

---

### Problem 3: No Crossover Signals

**Symptoms:** Strategy only trades on crossovers, misses trend-following opportunities.

**Root Cause:** Original code only executed orders on SMA crossover events, not on ongoing trends.

**Original Code (Broken):**
```python
# Only triggers on crossover
if cross_over:
    self.buy(...)
elif cross_under:
    self.sell(...)
# No trading when price is above/below SMA but no crossover
```

**Fixed Code (cta_strategies.py lines 393-403):**
```python
else:
    # Trend-following fallback when no crossover
    if self.pos == 0:
        if self.fast_ma > self.slow_ma:
            self.buy(bar.close_price, self.fixed_size)
        elif self.fast_ma < self.slow_ma:
            self.short(bar.close_price, self.fixed_size)
    elif self.pos > 0 and self.fast_ma < self.slow_ma:
        self.sell(bar.close_price, abs(self.pos))
    elif self.pos < 0 and self.fast_ma > self.slow_ma:
        self.cover(bar.close_price, abs(self.pos))
```

**Location Applied:** `cta_strategies.py` in `RlEnhancedCtaStrategy.on_bar()`

---

### Problem 4: Position Tracking in Mock

**Symptoms:** Trade positions not updating correctly.

**Root Cause:** MockCtaEngine wasn't updating strategy position.

**Fixed Code (conftest.py:231-239):**
```python
# Update strategy position
if direction == Direction.LONG and offset == Offset.OPEN:
    strategy.pos += volume
elif direction == Direction.SHORT and offset == Offset.OPEN:
    strategy.pos -= volume
elif direction == Direction.SHORT and offset == Offset.CLOSE:
    strategy.pos -= volume
elif direction == Direction.LONG and offset == Offset.CLOSE:
    strategy.pos += volume
```

**Location Applied:** `conftest.py` in `MockCtaEngine.send_order()`

---

## Writing New Tests

### Template

```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_rl_agent():
    """Create mock RL agent."""
    agent = Mock()
    agent.get_action_with_risk.return_value = {
        "action": "buy",
        "action_idx": 1,
        "evaluation": {"expected_pnl": 100, "risk_metrics": {}},
        "market_state": {},
        "timestamp": 0
    }
    return agent


@patch('vnpy_local.rl_module.get_rl_agent', create=True)
def test_new_feature(self, mock_get_rl, mock_cta_engine, mock_rl_agent):
    """Description of what this test verifies."""
    # Setup mock
    mock_get_rl.return_value = mock_rl_agent
    
    # Import strategy
    from vnpy_local.strategies.cta_strategies import RlEnhancedCtaStrategy
    
    # Create strategy
    strategy = RlEnhancedCtaStrategy(
        cta_engine=mock_cta_engine,
        strategy_name="TestNew",
        vt_symbol="BTCUSDT.BINANCE",
        setting={
            "fast_window": 5,
            "slow_window": 15,
            "fixed_size": 1,
            "rl_enabled": True
        }
    )
    
    # CRITICAL: Initialize and set trading!
    strategy.on_init()
    strategy.trading = True
    
    # Generate test data
    gen = SyntheticDataGenerator(initial_price=50000)
    bars = gen.generate_trending_bars(n=200, trend="up")
    
    # Run strategy
    for bar in bars:
        strategy.on_bar(bar)
    
    # Assertions
    assert strategy.inited is True
    assert len(mock_cta_engine.trades) > 0
```

---

## Debugging

### View Detailed Output

```bash
# Show all print statements
pytest tests/test_rl_cta_integration.py -v -s

# Show full traceback
pytest tests/test_rl_cta_integration.py -v --tb=long

# Stop on first failure
pytest tests/test_rl_cta_integration.py -v -x
```

### Interactive Debugging

```bash
# Drop into debugger on failure
pytest tests/test_rl_cta_integration.py -v --pdb

# Drop into debugger on first failure
pytest tests/test_rl_cta_integration.py -v -x --pdb
```

### Check State

```python
# Add to test to inspect state
print(f"Strategy state: inited={strategy.inited}, trading={strategy.trading}")
print(f"Position: {strategy.pos}")
print(f"Orders: {strategy.cta_engine.trades}")
print(f"Logs: {strategy.cta_engine.logs}")
```

---

## Common Test Failures

| Error | Cause | Fix |
|-------|-------|-----|
| `trading=False` orders not executing | CtaTemplate blocks orders | Add `strategy.trading = True` |
| `am.inited=False` | Not enough bars | Use 100+ bars |
| Position not resetting | Strategy reused | Create new strategy |
| Mock not called | Patch path wrong | Check `@patch` path |
| AttributeError: NoneType | Import error | Check `sys.path` |

---

## Test Results

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: /home/ubuntu
collected 10 items

test_rl_agent_loads PASSED                                          [ 10%]
test_cta_signal_validated_by_rl PASSED                              [ 20%]
test_rl_filter_approves_valid_signals PASSED                        [ 30%]
test_rl_filter_rejects_invalid_signals PASSED                      [ 40%]
test_fallback_when_rl_disabled PASSED                               [ 50%]
test_fallback_on_rl_error PASSED                                   [ 60%]
test_rl_reduces_whipsaws PASSED                                    [ 70%]
test_rl_preserves_trend_following PASSED                           [ 80%]
test_full_trading_cycle PASSED                                      [ 90%]
test_multiple_strategies_compare PASSED                            [100%]

============================== 10 passed in 1.63s ==============================
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Test VNPY Engine

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          python -m venv venv
          source venv/bin/activate
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          cd vnpy_engine
          pytest tests/test_rl_cta_integration.py -v
```

---

## File Locations

| File | Purpose |
|------|---------|
| `vnpy_engine/tests/test_rl_cta_integration.py` | Main test file (10 tests) |
| `vnpy_engine/tests/conftest.py` | Test fixtures |
| `vnpy_engine/tests/__init__.py` | Test package init |
| `vnpy_engine/.pytest_cache/` | Pytest cache |

---

## Related Documentation

- [VNPY_ENGINE.md](VNPY_ENGINE.md) - Complete engine documentation
- [ARCHITECTURE-DIAGRAMS.md](ARCHITECTURE-DIAGRAMS.md) - System architecture
