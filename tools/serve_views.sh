#!/bin/bash
# Serve view/ on http://127.0.0.1:8768/ so the viewers open in VS Code's
# Simple Browser (which cannot load file:// pages). Idempotent: leaves a
# running server alone.
cd "$(dirname "$0")/.." || exit 1
if curl -s -o /dev/null http://127.0.0.1:8768/; then echo "already serving view/ on http://127.0.0.1:8768/"; exit 0; fi
nohup python3 -m http.server 8768 --bind 127.0.0.1 --directory view > /tmp/gears_views_server.log 2>&1 &
disown
sleep 1
curl -s -o /dev/null http://127.0.0.1:8768/ && echo "serving view/ on http://127.0.0.1:8768/ (log /tmp/gears_views_server.log)"
