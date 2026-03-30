-- Financial Orchestrator PostgreSQL Schema
-- Created for trading system with modular architecture

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- TABLE: trades
-- Core trade execution history
-- =====================================================
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    trade_id VARCHAR(50) UNIQUE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('LONG', 'SHORT')),
    quantity DECIMAL(20, 8) NOT NULL,
    entry_price DECIMAL(20, 8),
    exit_price DECIMAL(20, 8),
    pnl DECIMAL(20, 8) DEFAULT 0,
    pnl_pct DECIMAL(10, 4) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed', 'cancelled')),
    strategy VARCHAR(50),
    regime VARCHAR(20),
    confidence DECIMAL(5, 4),
    score DECIMAL(5, 4),
    stop_loss DECIMAL(20, 8),
    take_profit DECIMAL(20, 8),
    explore_exploit VARCHAR(10) DEFAULT 'exploit' CHECK (explore_exploit IN ('explore', 'exploit')),
    executed_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for trades
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_status ON trades(status);
CREATE INDEX idx_trades_executed_at ON trades(executed_at);
CREATE INDEX idx_trades_regime ON trades(regime);
CREATE INDEX idx_trades_strategy ON trades(strategy);

-- =====================================================
-- TABLE: decisions
-- Every decision made by the trading system
-- =====================================================
CREATE TABLE IF NOT EXISTS decisions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    symbol VARCHAR(20),
    price DECIMAL(20, 8),
    regime VARCHAR(20),
    strategy VARCHAR(50),
    action VARCHAR(10) CHECK (action IN ('buy', 'sell', 'hold')),
    confidence DECIMAL(5, 4),
    score DECIMAL(5, 4),
    risk_passed BOOLEAN DEFAULT true,
    rejected_reason VARCHAR(200),
    explore_exploit VARCHAR(10) DEFAULT 'exploit',
    layer_outputs JSONB,
    metadata JSONB
);

-- Indexes for decisions
CREATE INDEX idx_decisions_timestamp ON decisions(timestamp);
CREATE INDEX idx_decisions_regime ON decisions(regime);
CREATE INDEX idx_decisions_action ON decisions(action);
CREATE INDEX idx_decisions_symbol ON decisions(symbol);

-- =====================================================
-- TABLE: metrics
-- Performance metrics over time
-- =====================================================
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    metric_type VARCHAR(50) NOT NULL,
    value DECIMAL(20, 8) NOT NULL,
    period VARCHAR(20) DEFAULT 'daily' CHECK (period IN ('intraday', 'daily', 'weekly', 'monthly')),
    metadata JSONB
);

-- Indexes for metrics
CREATE INDEX idx_metrics_type ON metrics(metric_type);
CREATE INDEX idx_metrics_timestamp ON metrics(timestamp);
CREATE INDEX idx_metrics_period ON metrics(period);

-- =====================================================
-- TABLE: regime_performance
-- Track performance by market regime
-- =====================================================
CREATE TABLE IF NOT EXISTS regime_performance (
    id SERIAL PRIMARY KEY,
    regime VARCHAR(20) UNIQUE NOT NULL,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    total_pnl DECIMAL(20, 8) DEFAULT 0,
    avg_pnl DECIMAL(20, 8),
    avg_confidence DECIMAL(5, 4),
    win_rate DECIMAL(5, 4),
    avg_holding_time_minutes DECIMAL(10, 2),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- TABLE: strategy_performance
-- Track performance by strategy
-- =====================================================
CREATE TABLE IF NOT EXISTS strategy_performance (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(50) UNIQUE NOT NULL,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    total_pnl DECIMAL(20, 8) DEFAULT 0,
    avg_pnl DECIMAL(20, 8),
    win_rate DECIMAL(5, 4),
    avg_confidence DECIMAL(5, 4),
    avg_score DECIMAL(5, 4),
    last_trade_at TIMESTAMP,
    last_updated TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- TABLE: system_events
-- System events, errors, restarts
-- =====================================================
CREATE TABLE IF NOT EXISTS system_events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('debug', 'info', 'warning', 'error', 'critical')),
    message TEXT,
    details JSONB,
    layer_name VARCHAR(30)
);

-- Indexes for system_events
CREATE INDEX idx_events_timestamp ON system_events(timestamp);
CREATE INDEX idx_events_type ON system_events(event_type);
CREATE INDEX idx_events_severity ON system_events(severity);
CREATE INDEX idx_events_layer ON system_events(layer_name);

-- =====================================================
-- TABLE: model_versions
-- ML model versioning for self-learning
-- =====================================================
CREATE TABLE IF NOT EXISTS model_versions (
    id SERIAL PRIMARY KEY,
    model_type VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    accuracy DECIMAL(5, 4),
    precision_score DECIMAL(5, 4),
    recall_score DECIMAL(5, 4),
    f1_score DECIMAL(5, 4),
    training_samples INTEGER,
    feature_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    file_path VARCHAR(200),
    metadata JSONB,
    UNIQUE(model_type, version)
);

-- Indexes for model_versions
CREATE INDEX idx_models_type ON model_versions(model_type);
CREATE INDEX idx_models_created ON model_versions(created_at);

-- =====================================================
-- TABLE: price_alerts
-- Price alert configurations
-- =====================================================
CREATE TABLE IF NOT EXISTS price_alerts (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    target_price DECIMAL(20, 8) NOT NULL,
    condition VARCHAR(10) NOT NULL CHECK (condition IN ('above', 'below')),
    alert_type VARCHAR(20) DEFAULT 'price' CHECK (alert_type IN ('price', 'percent', 'volume')),
    triggered BOOLEAN DEFAULT false,
    triggered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    user_id VARCHAR(50)
);

-- =====================================================
-- TABLE: layer_health
-- Track health of each layer
-- =====================================================
CREATE TABLE IF NOT EXISTS layer_health (
    id SERIAL PRIMARY KEY,
    layer_name VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('healthy', 'degraded', 'unhealthy', 'disabled')),
    last_check TIMESTAMP DEFAULT NOW(),
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    metadata JSONB
);

-- =====================================================
-- TABLE: positions (real-time, cached in Redis but persisted)
-- Current open positions
-- =====================================================
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('LONG', 'SHORT')),
    quantity DECIMAL(20, 8) NOT NULL,
    entry_price DECIMAL(20, 8) NOT NULL,
    current_price DECIMAL(20, 8),
    unrealized_pnl DECIMAL(20, 8) DEFAULT 0,
    leverage INTEGER DEFAULT 1,
    margin DECIMAL(20, 8),
    opened_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for positions
CREATE INDEX idx_positions_symbol ON positions(symbol);
CREATE INDEX idx_positions_side ON positions(side);

-- =====================================================
-- FUNCTION: update_updated_at()
-- Auto-update updated_at timestamp
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for auto-update
CREATE TRIGGER update_trades_updated_at
    BEFORE UPDATE ON trades
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_positions_updated_at
    BEFORE UPDATE ON positions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- =====================================================
-- VIEW: daily_performance_summary
-- Quick view of daily performance
-- =====================================================
CREATE OR REPLACE VIEW daily_performance_summary AS
SELECT 
    DATE(executed_at) as trade_date,
    COUNT(*) as total_trades,
    COUNT(*) FILTER (WHERE pnl > 0) as winning_trades,
    COUNT(*) FILTER (WHERE pnl < 0) as losing_trades,
    SUM(pnl) as total_pnl,
    AVG(pnl) as avg_pnl,
    AVG(pnl_pct) as avg_pnl_pct,
    MAX(pnl) as best_trade,
    MIN(pnl) as worst_trade
FROM trades
WHERE status = 'closed'
GROUP BY DATE(executed_at)
ORDER BY trade_date DESC;

-- =====================================================
-- VIEW: layer_health_summary
-- Current health status of all layers
-- =====================================================
CREATE OR REPLACE VIEW layer_health_summary AS
SELECT 
    layer_name,
    status,
    last_check,
    error_count,
    last_error
FROM layer_health
WHERE (layer_name, last_check) IN (
    SELECT layer_name, MAX(last_check)
    FROM layer_health
    GROUP BY layer_name
);

-- =====================================================
-- INSERT initial layer health records
-- =====================================================
INSERT INTO layer_health (layer_name, status, last_check) VALUES
    ('data', 'healthy', NOW()),
    ('features', 'healthy', NOW()),
    ('state', 'healthy', NOW()),
    ('strategy', 'healthy', NOW()),
    ('intelligence', 'healthy', NOW()),
    ('scoring', 'healthy', NOW()),
    ('risk', 'healthy', NOW()),
    ('execution', 'healthy', NOW()),
    ('memory', 'healthy', NOW()),
    ('output', 'healthy', NOW())
ON CONFLICT (layer_name) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trader;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trader;

-- Comments
COMMENT ON TABLE trades IS 'Trade execution history - core trading table';
COMMENT ON TABLE decisions IS 'Every decision made by the trading system';
COMMENT ON TABLE metrics IS 'Performance metrics over time';
COMMENT ON TABLE system_events IS 'System events, errors, restarts';
COMMENT ON TABLE model_versions IS 'ML model versioning for self-learning';

-- =====================================================
-- MIGRATION NOTE:
-- After 15 days: Migrate DuckDB trade history to PostgreSQL
-- Then deprecate DuckDB for trade/decision storage
-- Keep DuckDB only for market data analytics
-- =====================================================
