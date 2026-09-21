#!/bin/bash

echo "========================================"
echo "      Codyssey 4-1 Demo"
echo "========================================"
echo

echo "[1] SSH 설정 확인"
echo "----------------------------------------"
grep -E "^[[:space:]]*Port |^[[:space:]]*PermitRootLogin " /etc/ssh/sshd_config 2>/dev/null
echo

echo "[2] SSH 리슨 포트 확인"
echo "----------------------------------------"
ss -tulnp | grep ":20022" || echo "20022 포트를 확인할 수 없습니다."
echo

echo "[3] 방화벽(UFW) 확인"
echo "----------------------------------------"
if grep -q "^ENABLED=yes" /etc/ufw/ufw.conf 2>/dev/null; then
    echo "[OK] UFW is active"
else
    echo "[FAIL] UFW is inactive"
fi
echo

echo "[4] 사용자 계정 확인"
echo "----------------------------------------"
id agent-admin
id agent-dev
id agent-test
echo

echo "[5] 그룹 확인"
echo "----------------------------------------"
getent group agent-common
getent group agent-core
echo

echo "[6] 디렉터리 권한 확인"
echo "----------------------------------------"
ls -ld /home/agent-admin/agent-app/upload_files
ls -ld /home/agent-admin/agent-app/api_keys
ls -ld /var/log/agent-app
echo

echo "[7] Agent 실행 상태 확인"
echo "----------------------------------------"
if pgrep -f "agent-app-linux-arm64" > /dev/null; then
    echo "[OK] Agent application is running"
else
    echo "[FAIL] Agent application is not running"
fi
echo

echo "[8] Agent 포트 확인"
echo "----------------------------------------"
if ss -lnt | grep -q ':15034 '; then
    echo "[OK] TCP port 15034 is LISTEN"
else
    echo "[FAIL] TCP port 15034 is not LISTEN"
fi
echo

echo "[9] monitor.sh 실행"
echo "----------------------------------------"
/home/agent-admin/agent-app/bin/monitor.sh
echo

echo "[10] monitor.log 확인"
echo "----------------------------------------"
tail -n 5 /var/log/agent-app/monitor.log
echo

echo "[11] Cron 설정 확인"
echo "----------------------------------------"
if crontab -l 2>/dev/null | grep -q "/home/agent-admin/agent-app/bin/monitor.sh"; then
    echo "[OK] Cron is configured"
    crontab -l 2>/dev/null | grep "/home/agent-admin/agent-app/bin/monitor.sh"
else
    echo "[FAIL] Cron is not configured"
fi
echo

echo "========================================"
echo "           Demo 완료"
echo "========================================"