#!/bin/bash
set -e

echo "=========================================="
echo "  VN.PY Autonomous Trading Engine"
echo "=========================================="

echo "Waiting for Redis..."
until redis-cli -h "${REDIS_HOST:-redis}" ping > /dev/null 2>&1; do
    echo "  Waiting for Redis..."
    sleep 2
done
echo "Redis is ready!"

export REDIS_HOST="${REDIS_HOST:-redis}"
export REDIS_PORT="${REDIS_PORT:-6379}"

echo "Starting API Gateway in background..."
python -m vnpy.api_gateway &
API_PID=$!

echo "Starting MainEngine..."
python -m vnpy.main_engine &
ENGINE_PID=$!

echo "Starting Watchdog..."
python -m vnpy.watchdog &
WATCHDOG_PID=$!

trap "kill $API_PID $ENGINE_PID $WATCHDOG_PID 2>/dev/null; exit" SIGINT SIGTERM

echo "=========================================="
echo "  All services started!"
echo "  API: http://localhost:8000"
echo "  Health: http://localhost:8000/health"
echo "=========================================="

wait
