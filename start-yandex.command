#!/bin/bash
cd "$(dirname "$0")" || exit 1
python3 dashboard_server.py &
server_pid=$!
sleep 1
open -a "Yandex" "http://127.0.0.1:8765/"
printf '\nCareer Agent is running. Press Ctrl+C to stop.\n'
wait "$server_pid"
