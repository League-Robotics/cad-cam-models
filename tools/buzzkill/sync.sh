#!/bin/sh
# deploy: copy the server scripts to Buzzkill.
# pull:   copy the designs saved on Buzzkill into solidcraft/buzzkill/, to open in the Mac app.
# vnc:    start the app in Buzzkill's virtual display and tunnel noVNC to localhost:6080.
HERE="$(cd "$(dirname "$0")" && pwd)"
case "$1" in
  deploy)
    ssh buzzkill 'mkdir -p ~/designs/gears/bin ~/designs/gears/view'
    rsync -a "$HERE/serve.py" "$HERE/viewer.html" "$HERE/solidcraft-remote.sh" "$HERE/gui.sh" buzzkill:designs/gears/bin/ ;;
  pull)
    mkdir -p "$HERE/../../solidcraft/buzzkill"
    rsync -av --include='*.solidcraft' --include='*.step' --include='*.png' --exclude='*' \
      buzzkill:designs/gears/ "$HERE/../../solidcraft/buzzkill/" ;;
  vnc)
    # Tunnel to noVNC on Buzzkill (gui.sh), then open http://localhost:6080/vnc.html?autoconnect=1&resize=scale
    ssh buzzkill 'sh ~/designs/gears/bin/gui.sh start'
    lsof -iTCP:6080 -sTCP:LISTEN >/dev/null || ssh -f -N -L 6080:127.0.0.1:6080 buzzkill ;;
  *) echo "usage: $0 deploy|pull|vnc" >&2; exit 1 ;;
esac
