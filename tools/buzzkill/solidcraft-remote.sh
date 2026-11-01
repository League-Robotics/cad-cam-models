#!/bin/sh
# Runs on Buzzkill: the SolidCraft MCP server on stdio, plus the live mesh
# viewer on port 8765 (started once, left running). .mcp.json runs this over ssh.
DIR="$HOME/designs/gears"
HERE="$(dirname "$0")"
mkdir -p "$DIR/view"
if ! ss -ltn | grep -q ':8765 '; then
  nohup python3 "$HERE/serve.py" "$DIR/view" --port 8765 >"$HERE/serve.log" 2>&1 </dev/null &
fi
# --gui: drive the app running in the VNC display (gui.sh) instead of a headless model.
if [ "$1" = "--gui" ]; then
  shift
  sh "$HERE/gui.sh" start >/dev/null 2>&1
  set -- --connect 127.0.0.1:7878 "$@"
fi
cd "$DIR" && exec solidcraft-cli mcp --allow-path "$DIR" "$@"
