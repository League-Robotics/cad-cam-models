#!/bin/sh
# Runs on Buzzkill: the SolidCraft app in a virtual display (:77) with its MCP
# control port on 7878, shown through VNC (5977) and noVNC (6080). Everything
# listens on localhost only; reach noVNC through an ssh tunnel.
#   gui.sh start|stop|status
D=:77
LOG="$HOME/designs/gears/bin/gui"
mkdir -p "$LOG" "$HOME/designs/gears"
up() { pgrep -u "$USER" -f "$1" >/dev/null; }

case "$1" in
  start)
    up "Xvfb $D" || { nohup Xvfb $D -screen 0 1600x1000x24 -nolisten tcp >"$LOG/xvfb.log" 2>&1 & sleep 1; }
    up "solidcraft --control 7878" || (cd "$HOME/designs/gears" &&
      DISPLAY=$D nohup solidcraft --control 7878 >"$LOG/solidcraft.log" 2>&1 &)
    up "x11vnc -display $D" || nohup x11vnc -display $D -localhost -rfbport 5977 -nopw \
      -forever -shared -quiet >"$LOG/x11vnc.log" 2>&1 &
    up "websockify.*6080" || nohup websockify --web /usr/share/novnc 127.0.0.1:6080 \
      127.0.0.1:5977 >"$LOG/websockify.log" 2>&1 &
    sleep 3
    # The window doesn't repaint for control commands until it has had an input event.
    DISPLAY=$D xdotool mousemove 800 500
    "$0" status ;;
  stop)
    pkill -u "$USER" -f "websockify.*6080"; pkill -u "$USER" -f "x11vnc -display $D"
    pkill -u "$USER" -f "solidcraft --control 7878"; pkill -u "$USER" -f "Xvfb $D" ;;
  status)
    for p in "Xvfb $D" "solidcraft --control 7878" "x11vnc -display $D" "websockify.*6080"; do
      up "$p" && echo "up    $p" || echo "DOWN  $p"
    done ;;
  *) echo "usage: $0 start|stop|status" >&2; exit 1 ;;
esac
