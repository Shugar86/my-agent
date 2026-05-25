#!/bin/bash
# My Agent CLI launcher
# Usage: agent [command] [options]

cd "$(dirname "$0")" || exit 1
python3 agent.py "$@"
