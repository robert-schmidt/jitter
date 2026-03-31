#!/bin/bash
# Jitter - standalone shell version
# Works using Terminal's Accessibility permission — no .app permissions needed.
# Usage: ./jitter.sh
# Stop: Ctrl+C

INTERVAL=120  # seconds between pulses

echo "Jitter running (pulse every ${INTERVAL}s). Press Ctrl+C to stop."
echo "Tip: minimize this Terminal window and forget about it."
echo ""

while true; do
    osascript -e 'tell application "System Events" to key code 56' 2>/dev/null
    echo "$(date '+%H:%M:%S') pulse sent"
    sleep $INTERVAL
done
