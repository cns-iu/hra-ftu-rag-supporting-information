#!/bin/bash

# Loop 5 times
for i in {1..5}; do
    echo "=== Starting round $i ==="

    python src\process-donor\clean-age_yearold\0-clean-ageyearold.py

    python src\process-donor\clean-age_yearold\1-merged.py

    ROUND_FILE="data\donor-meta\age_yearold\round.csv"
    ROUND_NUM=$(head -n 1 "$ROUND_FILE" | awk -F',' '{print $1}')
    echo "Current round: $ROUND_NUM"

    if [ "$ROUND_NUM" -eq 1 ]; then
        echo "Round is 1, updating to 2 and skipping analyse-same.py"
        echo "2" > "$ROUND_FILE"
    else
        echo "Round is greater than 1, running analyse-same.py"
        python src\process-donor\clean-age_yearold\2-analyse-same.py
    fi

    echo "=== Finished round $i ==="
    echo
Done

echo "All 5 rounds completed."
