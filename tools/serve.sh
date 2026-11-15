#!/bin/bash
# Serve out/ on http://127.0.0.1:8771/ (drawings, views, the 3D viewer). Idempotent.
cd "$(dirname "$0")/.." || exit 1
mkdir -p out
if curl -s -o /dev/null http://127.0.0.1:8771/; then echo "already serving on http://127.0.0.1:8771/"; exit 0; fi
nohup python3 -m http.server 8771 --bind 127.0.0.1 --directory out > /tmp/robot_display_server.log 2>&1 &
disown
sleep 1
curl -s -o /dev/null http://127.0.0.1:8771/ && echo "serving out/ on http://127.0.0.1:8771/"
