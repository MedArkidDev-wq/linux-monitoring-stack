#!/bin/bash
set -e

echo "========================================"
echo "  LOAD SIMULATION"
echo "  Generating CPU stress + HTTP traffic"
echo "========================================"
echo ""

TARGET="http://localhost"

echo "[1/3] Sending 500 requests to / ..."
for i in $(seq 1 500); do
    curl -s -o /dev/null "$TARGET/"
    if [ $((i % 100)) -eq 0 ]; then
        echo "  Sent $i requests..."
    fi
done
echo "  Done."
echo ""

echo "[2/3] Sending 200 requests to /slow (testing latency)..."
for i in $(seq 1 200); do
    curl -s -o /dev/null "$TARGET/slow" &
    if [ $((i % 50)) -eq 0 ]; then
        wait
        echo "  Sent $i slow requests..."
    fi
done
wait
echo "  Done."
echo ""

echo "[3/3] Sending 100 requests to /error (testing error rates)..."
for i in $(seq 1 100); do
    curl -s -o /dev/null "$TARGET/error"
done
echo "  Done."
echo ""

echo "========================================"
echo "  Load test complete!"
echo "  Check Grafana: http://localhost:3000"
echo "========================================"
