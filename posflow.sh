#!/bin/bash
# PosFlow launcher — runs independently of terminal
cd "$(dirname "$0")"
source venv/bin/activate
nohup python main.py > logs/posflow.log 2>&1 &
echo "PosFlow started (PID $!)"
echo "Logs: $(pwd)/logs/posflow.log"
