#!/bin/bash

# Loop 5 times
for i in {1..5}; do
    echo "=== Starting round $i ==="

    # 1. Change to the "$all" directory and run clean-species.py
    python src\process-donor\clean-species\0-clean-species.py

    # 2. Change to the species directory and run merged.py
    python src\process-donor\clean-species\1-merged.py

    # 3. Check the round number in round.csv
    ROUND_FILE="data\donor-meta\species\round.csv"
    ROUND_NUM=$(head -n 1 "$ROUND_FILE" | awk -F',' '{print $1}')
    echo "Current round: $ROUND_NUM"

    if [ "$ROUND_NUM" -eq 1 ]; then
        echo "Round is 1, updating to 2 and skipping analyse-same.py"
        echo "2" > "$ROUND_FILE"
    else
        echo "Round is greater than 1, running analyse-same.py"
        python src\process-donor\clean-species\1-merged.py
    fi

    echo "=== Finished round $i ==="
    echo
Done

echo "All 5 rounds completed."
