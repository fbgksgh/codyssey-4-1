#!/bin/bash

if pgrep -f "agent-app-linux-arm64" > /dev/null; then
    echo "[OK] Agent application is running"
else
    echo "[FAIL] Agent application is not running"
    exit 1
fi

if ss -lnt | grep -q ':15034 '; then
    echo "[OK] TCP port 15034 is LISTEN"
else
    echo "[FAIL] TCP port 15034 is not LISTEN"
    exit 1
fi

if [ -f /etc/ufw/ufw.conf ] && grep -q "^ENABLED=yes" /etc/ufw/ufw.conf; then
    echo "[OK] UFW is active"
else
    echo "[WARNING] UFW is inactive"
fi

CPU=$(top -bn1 | awk -F',' '/Cpu\(s\)/ {gsub(/[^0-9.]/,"",$4); print 100-$4}')
echo "CPU: ${CPU}%"

MEM=$(free | awk '/Mem:/ {print ($3/$2)*100}')
echo "MEM: ${MEM}%"

DISK_USED=$(df / | awk 'NR==2 {print $5}' | tr -d '%')
echo "DISK_USED: ${DISK_USED}%"

if awk "BEGIN {exit !($CPU > 20)}"; then
    echo "[WARNING] CPU usage is above 20%"
fi

if awk "BEGIN {exit !($MEM > 10)}"; then
    echo "[WARNING] Memory usage is above 10%"
fi

if [ "$DISK_USED" -gt 80 ]; then
    echo "[WARNING] Disk usage is above 80%"
fi

PID=$(pgrep -f "agent-app-linux-arm64" | head -n 1)
LOG_FILE="/var/log/agent-app/monitor.log"
MAX_SIZE=10485760
if [ -f "$LOG_FILE" ] && [ "$(stat -c%s "$LOG_FILE")" -ge "$MAX_SIZE" ]; then
    rm -f "$LOG_FILE.10"
    for i in 9 8 7 6 5 4 3 2 1; do
        if [ -f "$LOG_FILE.$i" ]; then
            mv "$LOG_FILE.$i" "$LOG_FILE.$((i+1))"
        fi
    done
    mv "$LOG_FILE" "$LOG_FILE.1"
    touch "$LOG_FILE"
    chown agent-admin:agent-core "$LOG_FILE"
fi

echo "[$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')] PID:$PID CPU:${CPU}% MEM:${MEM}% DISK_USED:${DISK_USED}%" >> "$LOG_FILE"
