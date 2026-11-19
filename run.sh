#!/usr/bin/env bash
#
# Mini OS Simulator - Launcher Script
# Runs the Mini OS desktop application.
#
# Usage:
#   ./run.sh
#
# This script:
#   1. Sets the working directory to the project root
#   2. Activates a virtual environment if one is present (.venv, venv, env, .env)
#   3. Runs main.py using python3.14 (or falls back to python3 / python)
#

set -euo pipefail

# Resolve the directory containing this script, so the script works
# regardless of where it is invoked from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Determine the Python interpreter to use.
# Priority:
#   1. Virtual environment python (if .venv, venv, env, or .env exists)
#   2. python3.14 (the project's tested interpreter)
#   3. python3
#   4. python
PYTHON=""

# Check for a virtual environment
for VENV_DIR in .venv venv env .env; do
    if [ -f "$SCRIPT_DIR/$VENV_DIR/bin/python" ]; then
        PYTHON="$SCRIPT_DIR/$VENV_DIR/bin/python"
        break
    fi
done

# Fall back to system interpreters
if [ -z "$PYTHON" ]; then
    if command -v python3.14 >/dev/null 2>&1; then
        PYTHON="python3.14"
    elif command -v python3 >/dev/null 2>&1; then
        PYTHON="python3"
    elif command -v python >/dev/null 2>&1; then
        PYTHON="python"
    else
        echo "Error: No Python interpreter found." >&2
        echo "Please install Python 3.8+ and try again." >&2
        exit 1
    fi
fi

echo "Using Python: $PYTHON"
echo "Project directory: $SCRIPT_DIR"
echo ""

# Run the application
exec "$PYTHON" main.py "$@"
