#!/bin/bash
set -e

# Create logs directory if it doesn't exist
mkdir -p /logs/verifier

# Check if solution.py exists
if [ ! -f /workspace/solution.py ]; then
    echo "0.0" > /logs/verifier/reward.txt
    echo "FAIL: solution.py not found"
    exit 1
fi

# Run the solution and capture output
output=$(python /workspace/solution.py 2>&1)

# Check if output is exactly "4"
if [ "$output" = "4" ]; then
    echo "1.0" > /logs/verifier/reward.txt
    echo "PASS: Correct output"
    exit 0
else
    echo "0.0" > /logs/verifier/reward.txt
    echo "FAIL: Expected '4' but got '$output'"
    exit 1
fi
