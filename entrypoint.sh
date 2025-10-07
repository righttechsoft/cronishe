#!/bin/bash

# Start scheduler in background
echo "Starting scheduler..."
python scheduler.py &
SCHEDULER_PID=$!

# Start webui in background
echo "Starting web UI..."
python webui.py &
WEBUI_PID=$!

# Function to handle shutdown
shutdown() {
    echo "Shutting down..."
    kill $SCHEDULER_PID 2>/dev/null
    kill $WEBUI_PID 2>/dev/null
    exit 0
}

# Trap SIGTERM and SIGINT
trap shutdown SIGTERM SIGINT

# Wait for both processes
echo "Cronishe started. Scheduler PID: $SCHEDULER_PID, WebUI PID: $WEBUI_PID"
echo "WebUI available at http://localhost:48080"

# Wait for any process to exit
wait -n

# If one process exits, kill the other and exit
echo "One process exited, shutting down..."
shutdown
