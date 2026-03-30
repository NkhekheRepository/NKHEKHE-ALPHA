# Financial Orchestrator - 15-Day Migration Reminder
# ================================================
# 
# IMPORTANT: This file serves as a reminder for the DuckDB to PostgreSQL migration.
#
# ==== MIGRATION DATE ====
# After 15 days from deployment, execute the following:
#
# 1. Migrate DuckDB trade history to PostgreSQL:
#    - Export trades from DuckDB
#    - Import into PostgreSQL 'trades' table
#
# 2. Migrate decisions from DuckDB to PostgreSQL:
#    - Export decisions from DuckDB  
#    - Import into PostgreSQL 'decisions' table
#
# 3. Deprecate DuckDB for trade/decision storage:
#    - Set 'duckdb.enabled: false' in unified.yaml
#    - Use PostgreSQL as single source of truth
#
# 4. Keep DuckDB ONLY for:
#    - Market data analytics
#    - Historical price data
#    - Time-series queries
#
# ==== VERIFICATION ====
# After migration, verify:
# - Trade history loads correctly in dashboard
# - Decision logs searchable in PostgreSQL
# - Performance metrics calculated correctly
# - No data loss during migration
#
# ==== ROLLBACK PLAN ====
# If issues occur:
# 1. Keep DuckDB enabled as backup
# 2. Run migration in test environment first
# 3. Maintain dual-write until confident
#
# ==== TASKS ====
# [ ] Export DuckDB trades to CSV
# [ ] Import trades to PostgreSQL
# [ ] Verify trade count matches
# [ ] Update unified.yaml to disable DuckDB for trades
# [ ] Run 24-hour monitoring
# [ ] Deprecate DuckDB trade tables
