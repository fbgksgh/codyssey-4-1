# 컴퓨터가 알아서 자기 상태를 점검하게 만들기

Linux 환경에서 서버의 기본 보안 및 네트워크 설정을 구성하고, 사용자와 그룹의 권한을 설정한 후 Agent 애플리케이션의 실행 상태와 시스템 자원을 자동으로 점검하는 환경을 구축하였다.

또한 `monitor.sh`와 `cron`을 이용하여 Agent의 상태를 주기적으로 확인하고 결과를 로그로 기록하도록 구성하였다.

---

# 1. 프로젝트 구성

```text
컴퓨터가 알아서 자기 상태를 점검하게 만들기/
├── README.md
├── main.py
└── monitor.sh
```

### 파일 설명

| 파일           | 설명                                                   |
| ------------ | ---------------------------------------------------- |
| `main.py`    | 시스템의 SSH, 방화벽, 사용자 및 그룹 등의 상태를 자동으로 점검하는 Python 프로그램 |
| `monitor.sh` | Agent 실행 상태와 시스템 자원을 주기적으로 점검하는 모니터링 스크립트            |
| `README.md`  | 과제 수행 내용과 검증 결과를 정리한 문서                              |

---

# 2. 기본 보안 및 네트워크 설정

Linux 환경에서 SSH와 방화벽을 설정하고 필요한 포트만 사용할 수 있도록 구성하였다.

## SSH 설정

SSH 포트를 기본 포트에서 `20022`로 변경하고 Root 계정의 원격 로그인을 차단하였다.

```text
SSH Port: 20022
PermitRootLogin: no
```

Root 원격 로그인을 차단한 이유는 외부에서 Root 계정으로 직접 접근하는 경로를 줄여 불필요한 권한 상승 위험을 낮추기 위해서이다.

`main.py`에서는 다음과 같은 Linux 설정 파일과 명령을 이용하여 해당 상태를 확인하도록 구현하였다.

```text
/etc/ssh/sshd_config
PermitRootLogin
ss -tulnp
```

또한 `ss` 명령을 이용하여 SSH 포트 `20022`가 실제 LISTEN 상태인지 확인하였다.

```text
20022 → SSH
```

---

## 방화벽 설정

UFW를 사용하여 Linux 환경의 방화벽을 구성하였다.

외부에서 필요한 서비스만 접근할 수 있도록 다음 포트를 사용하였다.

| 포트        | 용도           |
| --------- | ------------ |
| TCP 20022 | SSH          |
| TCP 15034 | Agent 애플리케이션 |

`main.py`에서는 UFW의 상태와 `20022/tcp`, `15034/tcp` 허용 여부를 확인하도록 구현하였다.

방화벽은 기본적으로 필요한 포트만 허용하는 방식으로 구성하여 불필요한 외부 접근을 줄이는 것을 목표로 하였다.

---

# 3. 사용자 및 그룹 구성

Agent 서비스를 역할별로 구분하여 관리할 수 있도록 사용자와 그룹을 구성하였다.

## 사용자

```text
agent-admin
agent-dev
agent-test
```

| 사용자           | 역할                |
| ------------- | ----------------- |
| `agent-admin` | Agent 실행 및 운영     |
| `agent-dev`   | 개발 및 모니터링 스크립트 관리 |
| `agent-test`  | 테스트               |

## 그룹

```text
agent-common
agent-core
```

| 사용자           | 그룹                       |
| ------------- | ------------------------ |
| `agent-admin` | agent-common, agent-core |
| `agent-dev`   | agent-common, agent-core |
| `agent-test`  | agent-common             |

실제 Linux 환경에서 `id` 명령을 이용하여 사용자별 UID, GID 및 그룹 구성을 확인하였다.

`main.py`에서도 다음 사용자와 그룹이 존재하는지 확인하도록 구현하였다.

```text
users = [
    "agent-admin",
    "agent-dev",
    "agent-test"
]

groups = [
    "agent-common",
    "agent-core"
]
```

---

# 4. Agent 디렉터리 및 최소 권한 구성

Agent 실행을 위한 기본 디렉터리를 다음과 같이 구성하였다.

```text
/home/agent-admin/agent-app/
├── agent-app-linux-arm64
├── upload_files/
├── api_keys/
└── bin/
    └── monitor.sh

/var/log/agent-app/
└── monitor.log
```

## upload_files

```text
/home/agent-admin/agent-app/upload_files
```

파일 업로드 및 공유를 위한 디렉터리이며 `agent-common` 그룹을 기준으로 접근하도록 구성하였다.

## api_keys

```text
/home/agent-admin/agent-app/api_keys
```

Agent 실행에 필요한 인증 파일을 저장하는 디렉터리이며 `agent-core` 그룹을 기준으로 접근하도록 구성하였다.

실제 사용한 인증 파일은 다음과 같다.

```text
/home/agent-admin/agent-app/api_keys/secret.key
```

## 로그 디렉터리

```text
/var/log/agent-app
```

Agent 및 모니터링 로그를 저장하며 `agent-core` 그룹을 기준으로 접근하도록 구성하였다.

### 최소 권한을 적용한 이유

인증 파일과 운영 로그는 모든 사용자가 접근할 필요가 없기 때문에 관련 작업이 필요한 사용자와 그룹을 중심으로 접근 범위를 제한하였다.

이를 통해 불필요한 파일 접근을 줄이고, 인증 정보 및 운영 로그가 필요 이상의 사용자에게 노출되는 것을 방지하는 것을 목표로 하였다.

---

# 5. Agent 실행 환경

Agent 실행에 필요한 환경 변수를 구성하였다.

```text
AGENT_HOME=/home/agent-admin/agent-app
AGENT_PORT=15034
AGENT_UPLOAD_DIR=$AGENT_HOME/upload_files
AGENT_KEY_PATH=$AGENT_HOME/api_keys
AGENT_LOG_DIR=/var/log/agent-app
```

Agent 실행 파일은 다음과 같다.

```text
/home/agent-admin/agent-app/agent-app-linux-arm64
```

Agent는 `agent-admin` 계정으로 실행하였다.

Root 계정으로 Agent를 실행하지 않고 별도의 운영 계정을 사용하여 서비스 실행 권한을 제한하였다.

---

# 6. Agent Boot Sequence 확인

Agent를 실행하면 시작 과정에서 다음 5가지 항목을 확인한다.

```text
>>> Starting Agent Boot Sequence...

[1/5] Checking User Account               [OK]
[2/5] Verifying Environment Variables     [OK]
[3/5] Checking Required Files             [OK]
[4/5] Checking Port Availability          [OK]
[5/5] Verifying Log Permission            [OK]

------------------------------------------------------------
All Boot Checks Passed!
Agent READY
```

5개의 Boot Check가 모두 `[OK]` 상태로 완료되는 것을 확인하였다.

최종적으로 다음 메시지가 출력되었다.

```text
Agent READY
```

Agent 실행 후 다음과 같이 `15034` 포트에서 서비스가 실행되는 것도 확인하였다.

```text
Agent listening at port 15034
```

### Boot Sequence 확인 의미

Boot Sequence에서는 사용자 계정, 환경 변수, 필요한 파일, 포트 사용 가능 여부, 로그 권한을 순서대로 확인한다.

따라서 Agent가 실행되기 전에 기본 실행 조건이 충족되었는지를 확인할 수 있다.

---

# 7. monitor.sh 구성

Agent의 상태와 시스템 자원을 자동으로 확인하기 위해 `monitor.sh`를 작성하였다.

파일 위치:

```text
/home/agent-admin/agent-app/bin/monitor.sh
```

## 주요 점검 항목

* Agent 프로세스 실행 여부
* TCP `15034` 포트 LISTEN 여부
* UFW 활성화 여부
* CPU 사용량
* 메모리 사용량
* 디스크 사용량

---

# 8. 프로세스 및 포트 점검

## Agent 프로세스 확인

Agent 프로세스가 실행 중인지 확인하기 위해 `pgrep`을 사용하였다.

```bash
pgrep -f "agent-app-linux-arm64"
```

`pgrep`은 실행 중인 프로세스를 이름 또는 패턴으로 검색하기 때문에 Agent 프로세스의 존재 여부를 확인하는 데 사용하였다.

프로세스가 존재하면 정상 상태로 판단하고 다음 메시지를 출력한다.

```text
[OK] Agent application is running
```

프로세스가 존재하지 않는 경우에는 다음과 같이 처리한다.

```text
[FAIL] Agent application is not running
```

그리고 `exit 1`을 사용하여 실패 상태를 반환한다.

### 프로세스가 종료된 경우

현재 `monitor.sh`는 프로세스가 존재하는지 여부까지 확인하며, 프로세스가 종료된 구체적인 원인을 자동으로 추적하지는 않는다.

실제 운영 환경에서는 다음과 같은 추가 정보를 확인할 수 있다.

```text
1. Agent 로그 확인
2. 프로세스 종료 여부 확인
3. 15034 포트 LISTEN 여부 확인
4. 환경 변수 확인
5. 필요한 파일 및 권한 확인
```

이를 통해 단순히 `[FAIL]`을 출력하는 것에서 나아가 종료 원인을 추적하는 방식으로 확장할 수 있다.

---

## TCP 포트 확인

Agent가 실제로 `15034` 포트를 사용하여 LISTEN 상태인지 확인하기 위해 `ss` 명령을 사용하였다.

```bash
ss -lnt
```

`ss`는 현재 Linux 시스템의 소켓 및 네트워크 연결 상태를 확인할 수 있기 때문에 포트 LISTEN 여부를 확인하는 데 사용하였다.

포트가 정상적으로 열려 있으면:

```text
[OK] TCP port 15034 is LISTEN
```

포트가 열려 있지 않으면:

```text
[FAIL] TCP port 15034 is not LISTEN
```

을 출력하고 `exit 1`로 종료한다.

### 프로세스는 존재하지만 포트가 열리지 않는 경우

프로세스가 존재하지만 `15034` 포트가 LISTEN 상태가 아니라면 다음 항목을 우선적으로 확인할 수 있다.

```text
1. Agent의 포트 바인딩 설정
2. AGENT_PORT 환경 변수
3. 다른 프로세스의 포트 사용 여부
4. Agent 실행 로그
5. 방화벽 설정
```

따라서 프로세스와 포트를 별도로 확인하여 단순 프로세스 실행 여부만으로 서비스 정상 여부를 판단하지 않도록 구성하였다.

---

# 9. 모니터링 기준 및 심각도

시스템 자원 사용량에 기준을 설정하여 일정 수준을 넘으면 경고 메시지를 출력하도록 구성하였다.

```text
CPU > 20%          → WARNING
MEM > 10%          → WARNING
DISK_USED > 80%    → WARNING
```

Agent 프로세스가 실행되지 않았거나 `15034` 포트가 LISTEN 상태가 아닌 경우에는 `[FAIL]`을 출력하고 종료한다.

반면 CPU, 메모리, 디스크 사용량은 기준을 초과하더라도 `[WARNING]`을 출력하고 모니터링을 계속한다.

### 운영상 구분

```text
[FAIL]
→ 서비스 자체가 정상적으로 동작하지 않는 상태
→ 스크립트 종료
→ 실제 운영 환경에서는 장애 알림 대상으로 연계 가능

[WARNING]
→ 서비스는 동작하지만 자원 사용량이 기준을 초과한 상태
→ 모니터링 계속
→ 실제 운영 환경에서는 알림 또는 추적 대상으로 연계 가능
```

현재 과제에서는 알림 시스템 자체를 별도로 구현하지 않았으며, 로그와 상태 메시지를 기반으로 추후 Slack, 이메일 등의 알림 시스템과 연계할 수 있도록 구분하였다.

---

# 10. 시스템 자원 확인

CPU, 메모리, 디스크 사용량은 Linux 기본 명령어를 이용하여 확인하였다.

```text
top  → CPU 사용량
free → 메모리 사용량
df   → 디스크 사용량
```

## CPU

```bash
top
```

`top`의 CPU 정보를 파싱하여 현재 CPU 사용량을 계산한다.

## 메모리

```bash
free
```

전체 메모리와 사용 중인 메모리를 이용하여 사용률을 계산한다.

## 디스크

```bash
df /
```

루트 파일 시스템의 사용량을 확인한다.

### 파싱 방식의 한계

현재 스크립트는 Linux 명령어의 출력 형식을 기준으로 필요한 값을 추출한다.

따라서 다음과 같은 환경에서는 파싱 결과가 달라질 가능성이 있다.

```text
- Linux 배포판별 명령 출력 차이
- 명령어 버전 차이
- 시스템 로케일 차이
- CPU 정보 출력 형식 변경
```

현재 과제에서는 지정된 Linux 환경을 기준으로 구현하였다.

실제 운영 환경에서는 `top`, `free`, `df`의 출력 형식에 의존하지 않고 전용 시스템 모니터링 도구나 표준화된 출력 옵션을 사용하는 방식으로 보완할 수 있다.

---

# 11. monitor.sh 실행 결과

실제 Agent가 실행 중인 상태에서 `monitor.sh`를 실행하여 상태를 확인하였다.

```text
[OK] Agent application is running
[OK] TCP port 15034 is LISTEN
[OK] UFW is active
CPU: 1.3%
MEM: 17.0678%
DISK_USED: 1%
[WARNING] Memory usage is above 10%
```

실행 결과를 통해 다음 항목을 확인하였다.

```text
[OK] Agent 실행 확인
[OK] TCP 15034 포트 확인
[OK] UFW 활성화 확인
[OK] CPU 사용량 확인
[OK] 메모리 사용량 확인
[OK] 디스크 사용량 확인
```

메모리 사용량은 설정된 기준인 `10%`를 초과하여 `[WARNING]`이 출력되었다.

---

# 12. 로그 기록

모니터링 결과는 다음 파일에 기록하도록 구성하였다.

```text
/var/log/agent-app/monitor.log
```

로그에는 다음과 같은 정보가 기록된다.

| 필드        | 의미                  |
| --------- | ------------------- |
| 시간        | 모니터링이 실행된 시각        |
| PID       | 실행 중인 Agent 프로세스 ID |
| CPU       | CPU 사용률             |
| MEM       | 메모리 사용률             |
| DISK_USED | 디스크 사용률             |

로그 형식은 다음과 같다.

```text
[YYYY-MM-DD HH:MM:SS] PID:프로세스ID CPU:사용률% MEM:사용률% DISK_USED:사용률%
```

예시:

```text
[2026-09-18 10:48:01] PID:373 CPU:0.7% MEM:18.6259% DISK_USED:1%
[2026-09-18 10:49:02] PID:373 CPU:0.7% MEM:16.3681% DISK_USED:1%
[2026-09-18 10:50:01] PID:373 CPU:0% MEM:17.8939% DISK_USED:1%
[2026-09-18 10:51:01] PID:373 CPU:0.7% MEM:17.1653% DISK_USED:1%
[2026-09-18 10:52:01] PID:373 CPU:0% MEM:16.5424% DISK_USED:1%
```

---

# 13. 로그 누적 방식

모니터링 결과는 `>>` 연산자를 이용하여 로그 파일에 추가한다.

```bash
echo "로그 내용" >> "$LOG_FILE"
```

### `>`와 `>>`의 차이

```text
>   → 기존 파일 내용을 덮어씀
>>  → 기존 내용을 유지하고 마지막에 내용을 추가함
```

모니터링 로그는 이전 기록을 계속 보존해야 하므로 `>>`를 사용하였다.

이를 통해 `cron`이 매분 실행되더라도 기존 모니터링 기록을 삭제하지 않고 계속 누적할 수 있다.

---

# 14. Cron을 이용한 자동 모니터링

`monitor.sh`를 사람이 직접 실행하지 않아도 주기적으로 실행할 수 있도록 `cron`을 구성하였다.

등록된 작업은 다음과 같다.

```text
* * * * * /home/agent-admin/agent-app/bin/monitor.sh
```

위 설정은 `monitor.sh`를 1분마다 실행한다.

Cron 설정 확인:

```text
* * * * * /home/agent-admin/agent-app/bin/monitor.sh
```

실제로 `monitor.log`를 확인하여 약 1분 간격으로 새로운 로그가 추가되는 것을 확인하였다.

```text
[2026-09-18 10:48:01] PID:373 CPU:0.7% MEM:18.6259% DISK_USED:1%
[2026-09-18 10:49:02] PID:373 CPU:0.7% MEM:16.3681% DISK_USED:1%
[2026-09-18 10:50:01] PID:373 CPU:0% MEM:17.8939% DISK_USED:1%
```

자동화 과정은 다음과 같다.

```text
cron
  ↓
monitor.sh 실행
  ↓
Agent 및 시스템 상태 확인
  ↓
monitor.log 기록
```

실제 운영에서는 장애 상태인 `[FAIL]`이나 반복적인 `[WARNING]`을 외부 알림 시스템과 연계하여 관리할 수 있다.

---

# 15. 로그 로테이션 정책

모니터링이 계속 실행되면 로그 파일의 크기가 계속 증가할 수 있기 때문에 `monitor.sh` 내부에 용량 기반 로그 로테이션 기능을 구현하였다.

## 현재 적용 방식

현재 과제에서는 별도의 `logrotate` 설정 파일을 사용하지 않고 `monitor.sh` 내부에서 직접 로그 로테이션을 수행한다.

로그 최대 크기는 다음과 같다.

```text
10MB
```

로그가 `10MB` 이상이 되면 기존 로그를 순환 저장한다.

```text
monitor.log
monitor.log.1
monitor.log.2
monitor.log.3
...
monitor.log.10
```

가장 오래된 `monitor.log.10`을 삭제한 후 기존 로그의 번호를 하나씩 증가시키고 현재 로그를 `monitor.log.1`로 이동한다.

### 스크립트 기반 방식을 선택한 이유

이번 과제에서는 별도의 시스템 설정 파일을 추가하지 않고 `monitor.sh` 하나에서 모니터링과 로그 관리를 함께 수행할 수 있도록 구성하였다.

장점:

```text
- 별도의 logrotate 설정 파일이 필요하지 않음
- monitor.sh만으로 동작 과정을 확인할 수 있음
- 로그 크기 기준을 코드에서 직접 확인할 수 있음
```

단점:

```text
- 로그 관리 로직을 직접 유지보수해야 함
- 운영 환경에서는 검증된 logrotate와 같은 전용 도구보다 관리 기능이 제한적일 수 있음
```

따라서 현재 구현은 과제 환경에 맞춘 방식이며, 실제 서버 운영 환경에서는 `logrotate`와 같은 전용 로그 관리 도구를 사용하는 방법도 고려할 수 있다.

---

# 16. 로그 급증에 대한 대응 정책

로그가 갑자기 증가하는 경우를 다음과 같이 구분하여 관리한다.

### 단기 대응

현재 로그 파일이 `10MB` 이상이 되면 즉시 로테이션을 수행한다.

```text
monitor.log
→ monitor.log.1
```

최대 `monitor.log.10`까지 유지하고 가장 오래된 로그는 삭제한다.

### 중기 대응

반복적으로 로그가 빠르게 증가한다면 로그 발생량과 `[WARNING]`, `[FAIL]` 발생 여부를 확인하여 원인을 확인한다.

```text
1. monitor.log 발생량 확인
2. WARNING/FAIL 발생 빈도 확인
3. Agent 상태 확인
4. 시스템 자원 사용량 확인
```

### 장기 대응

실제 운영 환경에서는 로그 파일을 서버 외부의 중앙 로그 시스템으로 전달하거나 `logrotate`와 같은 전용 로그 관리 도구를 사용하는 방식으로 확장할 수 있다.

현재 과제에서는 로컬 로그의 용량 증가를 제어하는 것까지 구현하였다.

---

# 17. 브루트포스 공격에 대한 기본 대응 방향

SSH 포트를 `20022`로 변경하고 Root 원격 로그인을 차단한 것은 외부의 불필요한 직접 접근을 줄이기 위한 기본적인 보안 설정이다.

다만 포트 변경만으로 브루트포스 공격 자체가 차단되는 것은 아니다.

현재 과제에서 구성한 범위에서는:

```text
SSH Port 20022
Root 원격 로그인 차단
UFW를 통한 허용 포트 제한
시스템 및 서비스 상태 모니터링
로그 기록
```

을 통해 기본적인 접근 제한과 상태 확인을 수행한다.

실제 운영 환경에서 브루트포스 공격에 대한 추가 대응이 필요하다면 SSH 인증 실패 로그를 분석하고 반복적인 공격 IP를 차단하거나 `fail2ban`과 같은 별도의 탐지·차단 도구를 연계할 수 있다.

현재 과제에서는 이러한 자동 차단 기능 자체를 구현하지 않았으며, 로그 기반 탐지 및 차단 시스템으로 확장할 수 있는 구조를 고려하였다.

---

# 18. 주요 명령어 선택 이유

## `pgrep`

```bash
pgrep -f "agent-app-linux-arm64"
```

Agent 프로세스가 실행 중인지 빠르게 확인하기 위해 사용하였다.

## `ss`

```bash
ss -lnt
```

Linux 시스템에서 TCP 포트의 LISTEN 상태를 확인하기 위해 사용하였다.

`netstat`보다 현재 Linux 환경에서 기본적으로 사용할 수 있는 `ss`를 사용하여 포트 상태를 확인하였다.

## `top`

```bash
top
```

실행 중인 시스템의 CPU 상태를 확인하기 위해 사용하였다.

## `free`

```bash
free
```

전체 메모리와 사용 중인 메모리를 확인하여 메모리 사용률을 계산하기 위해 사용하였다.

## `df`

```bash
df /
```

파일 시스템의 디스크 사용량을 확인하기 위해 사용하였다.

---

# 19. 시스템 상태 자동 점검 프로그램

`main.py`는 현재 컴퓨터의 시스템 상태를 자동으로 확인하기 위한 Python 프로그램이다.

Linux 환경에서 과제의 요구사항에 해당하는 시스템 상태를 확인하도록 구성하였다.

주요 점검 대상은 다음과 같다.

```text
SSH 포트
Root 원격 로그인 설정
SSH LISTEN 상태
방화벽 상태
방화벽 허용 포트
허용 포트 제한
사용자 계정
그룹
그룹 구성원
```

Mac 환경에서는 Linux 전용 명령을 사용할 수 없기 때문에 해당 항목을 `SKIP` 처리하도록 구성하였다.

실행 시 다음과 같이 출력된다.

```text
[SSH 포트 점검]
SKIP - Linux 환경이 아니므로 ...

[Root 원격 로그인 점검]
SKIP - Linux 환경이 아니므로 ...

[SSH 리슨 포트 점검]
SKIP - Linux 환경이 아니므로 ...

[방화벽 점검]
SKIP - Linux 환경이 아니므로 ...

[방화벽 허용 포트 점검]
SKIP - Linux 환경이 아니므로 ...

[허용 포트 제한 점검]
SKIP - Linux 환경이 아니므로 ...
```

---

# 20. 개발 환경

이번 과제의 개발 및 Git 관리 환경은 MacBook을 사용하였다.

Mac에서는 Linux 전용 SSH, UFW, 사용자 및 그룹 설정을 직접 수행하기 어려웠기 때문에 Linux 환경에서 필요한 작업을 수행하고 검증하였다.

Python 프로그램과 GitHub 저장소 관리는 Mac 환경에서 진행하였다.

| 환경       | 작업                                      |
| -------- | --------------------------------------- |
| Mac      | Python 코드 작성, Git 관리, GitHub 업로드        |
| Linux 환경 | SSH, UFW, 사용자/그룹, Agent, Cron 및 모니터링 검증 |

---

# 21. 최종 확인

이번 과제를 통해 다음과 같은 항목을 구성하고 확인하였다.

```text
[OK] SSH Port 20022 설정
[OK] Root 원격 로그인 차단
[OK] SSH LISTEN 상태 확인
[OK] UFW 방화벽 활성화
[OK] TCP 20022 포트 설정
[OK] TCP 15034 포트 설정

[OK] agent-admin 계정 구성
[OK] agent-dev 계정 구성
[OK] agent-test 계정 구성
[OK] agent-common 그룹 구성
[OK] agent-core 그룹 구성
[OK] 그룹 구성원 확인

[OK] AGENT_HOME 구성
[OK] upload_files 구성
[OK] api_keys 구성
[OK] /var/log/agent-app 구성
[OK] 최소 권한 기반 디렉터리 구성

[OK] Agent 환경 변수 설정
[OK] Agent Boot Sequence 5단계 통과
[OK] Agent READY 확인
[OK] TCP 15034 LISTEN 확인

[OK] monitor.sh 작성
[OK] Agent 프로세스 점검
[OK] 포트 점검
[OK] UFW 상태 점검
[OK] CPU 점검
[OK] 메모리 점검
[OK] 디스크 점검
[OK] monitor.log 기록

[OK] 로그 누적 기록
[OK] 10MB 기준 로그 로테이션
[OK] 최대 10개 백업 로그 유지
[OK] cron 1분 주기 실행
[OK] monitor.log 주기적 기록 확인
```

---

# 22. 마무리

이번 과제에서는 Linux 환경의 기본적인 보안 및 네트워크 설정부터 사용자와 그룹 권한 구성, Agent 실행, 시스템 자원 모니터링, 로그 관리, 자동 실행까지 구성하였다.

특히 `monitor.sh`와 `cron`을 이용하여 사람이 직접 확인하지 않아도 Agent의 실행 상태와 시스템 자원 사용량을 주기적으로 확인하고 로그로 남길 수 있도록 구성하였다.

또한 프로세스와 포트를 별도로 확인하여 서비스가 실제로 정상 동작하고 있는지 확인하도록 구성하였으며, CPU·메모리·디스크 사용량은 `WARNING`, 서비스 자체의 장애는 `FAIL`로 구분하였다.

로그는 `>>`를 사용하여 기존 기록을 유지하면서 누적하고, 10MB 이상 증가하면 스크립트 내부의 로테이션 기능을 이용하여 로그 파일을 순환 관리하도록 구성하였다.

현재 과제에서는 스크립트 기반 로그 관리와 기본적인 상태 모니터링까지 구현하였으며, 실제 운영 환경에서는 중앙 로그 시스템, `logrotate`, 브루트포스 탐지 및 자동 알림 시스템 등과 연계하여 확장할 수 있다.

이를 통해 Linux 서버 환경에서 시스템 상태를 자동으로 확인하고 관리하는 기본적인 운영 자동화 환경을 구축하였다.
