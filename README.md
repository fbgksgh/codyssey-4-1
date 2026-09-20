# 컴퓨터가 알아서 자기 상태를 점검하게 만들기

Linux 서버 환경에서 기본 보안 및 네트워크 설정을 구성하고, 사용자 및 그룹 권한을 설정한 후 실행 중인 Agent의 상태를 자동으로 점검하는 환경을 구축하였다.

또한 `monitor.sh`와 `cron`을 이용하여 Agent의 실행 상태와 시스템 자원 사용량을 주기적으로 확인하고, 결과를 로그로 기록하도록 구성하였다.

---

# 1. 기본 보안 및 네트워크 설정

## SSH 포트 변경 및 Root 원격 로그인 차단

SSH 기본 포트를 `20022`로 변경하고 Root 계정의 원격 로그인을 차단하였다.

### 설정 내용

```text
SSH Port: 20022
PermitRootLogin: no
```

### 주요 설정 명령

```bash
sudo nano /etc/ssh/sshd_config
```

수정 내용:

```text
Port 20022
PermitRootLogin no
```

설정 파일의 문법 오류를 확인한 후 SSH 서비스를 실행하였다.

```bash
sudo sshd -t
sudo service ssh start
```

### SSH 포트 확인

```bash
ss -tulnp | grep 20022
```

`20022` 포트가 LISTEN 상태인 것을 확인하였다.

---

## UFW 방화벽 설정

UFW 방화벽을 활성화하고 필요한 포트만 허용하였다.

### 허용 포트

| 포트        | 용도           |
| --------- | ------------ |
| TCP 20022 | SSH          |
| TCP 15034 | Agent 애플리케이션 |

### 방화벽 설정

```bash
sudo apt install ufw -y

sudo ufw default deny incoming
sudo ufw default allow outgoing

sudo ufw allow 20022/tcp
sudo ufw allow 15034/tcp

sudo ufw enable
```

### 상태 확인

```bash
sudo ufw status verbose
```

설정 후 `20022/tcp`, `15034/tcp` 포트가 허용된 것을 확인하였다.

---

# 2. 사용자 및 그룹 권한 구성

## 사용자 및 그룹

서비스 운영과 협업을 구분하기 위해 다음 사용자와 그룹을 생성하였다.

### 사용자

* `agent-admin` : Agent 실행 및 운영 담당
* `agent-dev` : 개발 및 `monitor.sh` 관리 담당
* `agent-test` : 테스트 담당

### 그룹

* `agent-common` : 공용 작업 및 파일 공유
* `agent-core` : 운영 및 핵심 파일 접근

### 그룹 구성

| 사용자         | 그룹                       |
| ----------- | ------------------------ |
| agent-admin | agent-common, agent-core |
| agent-dev   | agent-common, agent-core |
| agent-test  | agent-common             |

### 확인

```bash
id agent-admin
id agent-dev
id agent-test
```

그룹 구성도 확인하였다.

```bash
grep -E 'agent-common|agent-core' /etc/group
```

---

# 3. 디렉터리 및 권한 구성

## 주요 디렉터리

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

`AGENT_HOME`은 다음 경로로 구성하였다.

```text
/home/agent-admin/agent-app
```

---

## 디렉터리별 권한

### upload_files

`agent-common` 그룹이 사용하는 공용 파일 업로드 디렉터리로 구성하였다.

```text
/home/agent-admin/agent-app/upload_files
```

### api_keys

Agent 실행에 필요한 키 파일을 저장하는 디렉터리이다.

```text
/home/agent-admin/agent-app/api_keys
```

`agent-core` 그룹을 기준으로 접근 권한을 설정하였다.

### 로그 디렉터리

```text
/var/log/agent-app
```

Agent 운영 로그를 저장하며 `agent-core` 그룹을 기준으로 접근 권한을 설정하였다.

### 권한 확인

```bash
ls -ld /home/agent-admin/agent-app/upload_files
ls -ld /home/agent-admin/agent-app/api_keys
ls -ld /var/log/agent-app
```

---

# 4. Agent 실행 환경 구성

## 환경 변수 설정

`agent-admin` 계정에서 Agent 실행에 필요한 환경 변수를 설정하였다.

```bash
export AGENT_HOME=/home/agent-admin/agent-app
export AGENT_PORT=15034
export AGENT_UPLOAD_DIR=$AGENT_HOME/upload_files
export AGENT_KEY_PATH=$AGENT_HOME/api_keys
export AGENT_LOG_DIR=/var/log/agent-app
```

환경 변수는 `~/.bashrc`에 등록하여 Bash 환경에서 사용할 수 있도록 구성하였다.

---

## Agent 인증 파일

Agent 실행에 필요한 키 파일을 다음 디렉터리에 구성하였다.

```text
/home/agent-admin/agent-app/api_keys/secret.key
```

실제 Agent가 해당 키 파일을 정상적으로 인식하는 것을 확인하였다.

---

## Agent 실행 조건

Agent는 Root 계정이 아닌 `agent-admin` 계정으로 실행하였다.

실행 파일:

```text
/home/agent-admin/agent-app/agent-app-linux-arm64
```

실행:

```bash
cd $AGENT_HOME
./agent-app-linux-arm64
```

---

# 5. Agent Boot Sequence 확인

Agent 실행 시 다음과 같은 5단계 Boot Sequence를 확인하였다.

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

모든 Boot Check가 `[OK]` 상태로 완료되었으며 최종적으로 `Agent READY`가 출력되는 것을 확인하였다.

또한 Agent 실행 후 `15034` 포트에서 LISTEN 상태가 되는 것을 확인하였다.

---

# 6. 시스템 관제 자동화 스크립트

## monitor.sh

Agent의 상태와 시스템 자원을 자동으로 확인하기 위해 `monitor.sh`를 작성하였다.

파일 위치:

```text
/home/agent-admin/agent-app/bin/monitor.sh
```

### 주요 점검 항목

* Agent 프로세스 실행 여부
* TCP `15034` 포트 LISTEN 여부
* UFW 활성화 여부
* CPU 사용량
* 메모리 사용량
* 디스크 사용량

---

## 상태 점검 기준

다음과 같은 기준을 적용하였다.

```text
CPU > 20%          → WARNING
MEM > 10%          → WARNING
DISK_USED > 80%    → WARNING
```

Agent 프로세스가 실행되지 않았거나 `15034` 포트가 LISTEN 상태가 아닌 경우에는 `[FAIL]`을 출력하고 종료하도록 구성하였다.

반면 CPU, 메모리, 디스크 사용량과 같은 자원 문제는 즉시 프로그램을 종료하지 않고 `[WARNING]`을 출력하도록 구성하였다.

---

## monitor.sh 실행 권한

`monitor.sh`는 `agent-dev`가 소유하고 `agent-core` 그룹이 실행할 수 있도록 권한을 설정하였다.

```bash
sudo chown agent-dev:agent-core /home/agent-admin/agent-app/bin/monitor.sh
sudo chmod 750 /home/agent-admin/agent-app/bin/monitor.sh
```

권한 확인:

```bash
ls -l /home/agent-admin/agent-app/bin/monitor.sh
```

권한 `750`의 의미:

```text
owner  : 읽기 / 쓰기 / 실행
group  : 읽기 / 실행
others : 접근 불가
```

---

# 7. monitor.sh 실행 결과

실제로 `monitor.sh`를 실행하여 Agent와 시스템 상태를 확인하였다.

```bash
/home/agent-admin/agent-app/bin/monitor.sh
```

실행 결과:

```text
[OK] Agent application is running
[OK] TCP port 15034 is LISTEN
[OK] UFW is active
CPU: 1.3%
MEM: 17.0678%
DISK_USED: 1%

[WARNING] Memory usage is above 10%
```

Agent가 정상적으로 실행되고 있으며 `15034` 포트도 LISTEN 상태인 것을 확인하였다.

메모리 사용량은 설정한 기준인 `10%`를 초과하여 `[WARNING]` 메시지가 출력되는 것도 확인하였다.

---

# 8. 로그 기록

모니터링 결과는 다음 파일에 기록하였다.

```text
/var/log/agent-app/monitor.log
```

로그에는 다음 정보가 포함된다.

```text
시간
PID
CPU 사용량
메모리 사용량
디스크 사용량
```

### 로그 예시

```text
[2026-09-18 10:48:01] PID:373 CPU:0.7% MEM:18.6259% DISK_USED:1%
[2026-09-18 10:49:02] PID:373 CPU:0.7% MEM:16.3681% DISK_USED:1%
[2026-09-18 10:50:01] PID:373 CPU:0% MEM:17.8939% DISK_USED:1%
[2026-09-18 10:51:01] PID:373 CPU:0.7% MEM:17.1653% DISK_USED:1%
[2026-09-18 10:52:01] PID:373 CPU:0% MEM:16.5424% DISK_USED:1%
```

로그를 시간 순서대로 누적하기 위해 `>>` 방식으로 기록하도록 구성하였다.

---

# 9. Cron을 이용한 자동 실행

수동으로 `monitor.sh`를 실행하는 것이 아니라 주기적으로 자동 실행되도록 `cron`을 설정하였다.

### Cron 등록

```bash
crontab -e
```

다음 내용을 등록하였다.

```text
* * * * * /home/agent-admin/agent-app/bin/monitor.sh
```

### 의미

```text
* * * * *
│ │ │ │ │
│ │ │ │ └── 요일
│ │ │ └──── 월
│ │ └────── 일
│ └──────── 시
└────────── 분
```

따라서 위 설정은 `1분마다 monitor.sh를 실행`한다.

### 등록 확인

```bash
crontab -l
```

결과:

```text
* * * * * /home/agent-admin/agent-app/bin/monitor.sh
```

---

## Cron 실행 확인

실제로 Cron이 동작하는지 확인하기 위해 `monitor.log`의 내용을 확인하였다.

약 1분 간격으로 새로운 로그가 추가되는 것을 확인하였다.

```text
[2026-09-18 10:48:01] PID:373 CPU:0.7% MEM:18.6259% DISK_USED:1%
[2026-09-18 10:49:02] PID:373 CPU:0.7% MEM:16.3681% DISK_USED:1%
[2026-09-18 10:50:01] PID:373 CPU:0% MEM:17.8939% DISK_USED:1%
```

이를 통해 `cron → monitor.sh → monitor.log` 형태로 자동 모니터링이 수행되는 것을 확인하였다.

---

# 10. 로그 로테이션

모니터링이 계속 실행되면 로그 파일이 계속 커질 수 있기 때문에 로그 크기를 확인하여 일정 크기 이상 증가하면 이전 로그를 순환 저장하도록 구성하였다.

### 로그 관리 기준

```text
최대 크기: 10MB
```

10MB 이상이 되면 기존 로그를 다음과 같은 형태로 이동한다.

```text
monitor.log
monitor.log.1
monitor.log.2
monitor.log.3
...
monitor.log.10
```

가장 오래된 로그를 제거하고 최근 로그를 보존하는 방식으로 구성하였다.

이를 통해 장기간 모니터링을 수행하더라도 로그 파일이 계속 증가하여 디스크 공간을 사용하는 문제를 방지할 수 있도록 하였다.

---

# 11. monitor.sh 설계 이유

## 프로세스 확인

Agent 프로세스가 실행 중인지 확인하기 위해 `pgrep`을 사용하였다.

```bash
pgrep -f "agent-app-linux-arm64"
```

프로세스가 존재하면 정상 상태로 판단하고, 존재하지 않으면 `[FAIL]`을 출력하도록 구성하였다.

---

## 포트 확인

Agent가 실제로 `15034` 포트를 사용하여 LISTEN 상태인지 확인하기 위해 `ss` 명령을 사용하였다.

```bash
ss -lnt
```

프로세스가 실행 중이더라도 포트가 열려 있지 않으면 정상적인 서비스 상태라고 보기 어렵기 때문에 프로세스와 포트를 각각 확인하도록 구성하였다.

---

## CPU / 메모리 / 디스크 확인

시스템 자원 사용량은 Linux 기본 명령어를 활용하여 확인하였다.

```text
top  → CPU 사용량
free → 메모리 사용량
df   → 디스크 사용량
```

각 결과에서 필요한 값을 추출하여 `monitor.log`에 기록하였다.

---

# 12. 장애 상태와 경고 상태 구분

모니터링 항목을 서비스에 직접적인 영향을 주는 상태와 자원 경고 상태로 구분하였다.

### 서비스 장애로 판단

```text
Agent 프로세스가 실행되지 않음
15034 포트가 LISTEN 상태가 아님
```

위와 같은 경우:

```text
[FAIL]
```

을 출력하고 종료한다.

### 경고로 판단

```text
CPU > 20%
MEM > 10%
DISK_USED > 80%
```

위와 같은 경우에는:

```text
[WARNING]
```

을 출력하고 모니터링을 계속 수행한다.

즉, 서비스 자체가 동작하지 않는 상태와 자원 사용량이 높은 상태를 구분하여 처리하도록 설계하였다.

---

# 13. Mac 환경에서의 확인

현재 개발 및 Git 관리 환경은 Mac이다.

하지만 SSH, UFW, Linux 사용자 및 그룹 등 일부 요구사항은 Linux 환경이 필요하기 때문에 Docker의 Ubuntu 환경에서 수행하였다.

Mac에서 Linux 전용 항목을 실행할 경우에는 Linux 환경이 아니므로 다음과 같이 `SKIP` 처리되도록 구성하였다.

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

Linux Docker 환경에서는 실제 SSH, UFW, 계정, 그룹, Agent 실행 및 Cron 설정을 수행하고 정상 동작을 확인하였다.

---

# 14. 최종 확인 내용

이번 과제를 통해 다음 항목을 구성하고 확인하였다.

```text
[OK] SSH Port 20022 설정
[OK] Root 원격 로그인 차단
[OK] UFW 방화벽 활성화
[OK] TCP 20022 포트 허용
[OK] TCP 15034 포트 허용

[OK] agent-admin 계정 구성
[OK] agent-dev 계정 구성
[OK] agent-test 계정 구성
[OK] agent-common 그룹 구성
[OK] agent-core 그룹 구성

[OK] AGENT_HOME 구성
[OK] upload_files 디렉터리 구성
[OK] api_keys 디렉터리 구성
[OK] /var/log/agent-app 구성

[OK] 환경 변수 설정
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
[OK] 로그 로테이션 구성
[OK] cron 1분 주기 실행
[OK] monitor.log 주기적 기록 확인
```

---

# 15. 프로젝트 파일

GitHub 저장소에는 다음 파일을 관리한다.

```text
컴퓨터가 알아서 자기 상태를 점검하게 만들기/
├── README.md
├── main.py
└── monitor.sh
```

### main.py

컴퓨터의 상태를 자동으로 점검하는 Python 프로그램이다.

Linux 환경에서는 요구사항에 따라 SSH, 방화벽, 사용자 및 그룹 등의 상태를 확인하며, Mac과 같이 Linux가 아닌 환경에서는 Linux 전용 항목을 `SKIP` 처리한다.

### monitor.sh

실행 중인 Agent의 상태와 CPU, 메모리, 디스크 사용량을 확인하고 결과를 로그에 기록하는 시스템 관제 스크립트이다.

### README.md

과제 수행 과정과 주요 설정, 실행 결과 및 검증 내용을 정리한 문서이다.

---

# 16. 마무리

이번 과제에서는 단순히 애플리케이션을 실행하는 것에서 끝나는 것이 아니라 Linux 환경에서 보안 설정, 사용자 및 그룹 권한, 애플리케이션 실행 환경, 시스템 자원 모니터링, 로그 관리, 자동 실행까지 구성하였다.

특히 `monitor.sh`와 `cron`을 이용하여 사람이 직접 확인하지 않아도 Agent의 상태와 시스템 자원 사용량을 주기적으로 확인하고 로그로 남길 수 있도록 구성하였다.

이를 통해 Linux 서버 환경에서 시스템 상태를 자동으로 확인하고 관리하는 기본적인 운영 환경을 구축하였다.
