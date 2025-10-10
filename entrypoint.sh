#!/bin/bash

# Environment variables to control which components to run
# RUN_SCHEDULER: true/false (default: true)
# RUN_WEBUI: true/false (default: true)
# RUN_MANAGER: true/false (default: false)

RUN_SCHEDULER=${RUN_SCHEDULER:-true}
RUN_WEBUI=${RUN_WEBUI:-true}
RUN_MANAGER=${RUN_MANAGER:-false}

PIDS=()
COMPONENTS=()

# Start scheduler if enabled
if [ "$RUN_SCHEDULER" = "true" ]; then
    echo "Starting scheduler..."
    python scheduler.py &
    SCHEDULER_PID=$!
    PIDS+=($SCHEDULER_PID)
    COMPONENTS+=("Scheduler:$SCHEDULER_PID")
    echo "  Scheduler started (PID: $SCHEDULER_PID)"
fi

# Start webui if enabled
if [ "$RUN_WEBUI" = "true" ]; then
    echo "Starting web UI..."
    python webui.py &
    WEBUI_PID=$!
    PIDS+=($WEBUI_PID)
    COMPONENTS+=("WebUI:$WEBUI_PID")
    echo "  WebUI started (PID: $WEBUI_PID) - available at http://localhost:48080"
fi

# Start manager if enabled
if [ "$RUN_MANAGER" = "true" ]; then
    echo "Starting manager..."
    python manager.py &
    MANAGER_PID=$!
    PIDS+=($MANAGER_PID)
    COMPONENTS+=("Manager:$MANAGER_PID")
    echo "  Manager started (PID: $MANAGER_PID) - available at http://localhost:${MANAGER_PORT:-48090}"
fi

# Check if any components are running
if [ ${#PIDS[@]} -eq 0 ]; then
    echo "ERROR: No components enabled. Set RUN_SCHEDULER=true, RUN_WEBUI=true, or RUN_MANAGER=true"
    exit 1
fi

# Function to handle shutdown
shutdown() {
    echo "Shutting down..."
    for pid in "${PIDS[@]}"; do
        kill $pid 2>/dev/null
    done
    exit 0
}

# Trap SIGTERM and SIGINT
trap shutdown SIGTERM SIGINT

# Display running components
echo ""
echo "Cronishe started with components:"
for comp in "${COMPONENTS[@]}"; do
    echo "  - $comp"
done
echo ""

# Wait for any process to exit
wait -n

# If one process exits, kill the others and exit
echo "One process exited, shutting down all components..."
shutdown
