#!/bin/bash
# Restart spotiAFK if it crashes; a clean exit (Ctrl-C / SIGTERM) stops the loop.
set -u
cd "$(dirname "$0")" || exit 1

delay=2
while true; do
    python3 spotiAFK.py && break
    echo "spotiAFK crashed, restarting in ${delay}s..." >&2
    sleep "$delay"
    # Exponential backoff, capped at 5 minutes
    delay=$((delay * 2))
    [ "$delay" -gt 300 ] && delay=300
done
