# codyssey-4-1

컴퓨터가 알아서 자기 상태를 점검하게 만들기

## 1. 과제 소개

Linux 환경에서 서버의 기본 보안 및 네트워크 설정을 구성하고, 사용자와 권한을 설정한 후 실행 중인 Agent의 상태를 자동으로 점검하는 환경을 구축 했습니다.

또한 `monitor.sh`와 cron을 이용하여 Agent의 프로세스, 포트, CPU, 메모리, 디스크 사용량 등을 주기적으로 확인하고 결과를 로그로 기록하도록 구현 했습니다.

## 2. 실행 환경

* Ubuntu 22.04
* Docker
* Bash
* Python 기반 제공 Agent 프로그램
* UFW
* OpenSSH
* cron

## 3. 주요 구현 내용

### 보안 및 네트워크

* SSH 포트 변경: `20022`
* Root 원격 로그인 차단
* UFW 방화벽 활성화
* TCP `20022` 포트 허용
* TCP `15034` 포트 허용
* SSH 포트가 정상적으로 LISTEN 상태인지 확인

### 사용자 및 그룹

사용자:

* `agent-admin`
* `agent-dev`
* `agent-test`

그룹:

* `agent-common`
* `agent-core`

그룹 구성:

* `agent-admin` → `agent-common`, `agent-core`
* `agent-dev` → `agent-common`, `agent-core`
* `agent-test` → `agent-common`

### 디렉터리 및 권한

주요 디렉터리:

```text
/home/agent-admin/agent-app
/home/agent-admin/agent-app/upload_files
/home/agent-admin/agent-app/api_keys
/var/log/agent-app
```

권한 설정:

* `upload_files` → `agent-common` 그룹에서 사용
* `api_keys` → `agent-core` 그룹에서 사용
* `/var/log/agent-app` → `agent-core` 그룹에서 사용

## 4. Agent 실행 환경

환경 변수:

```bash
AGENT_HOME=/home/agent-admin/agent-app
AGENT_PORT=15034
AGENT_UPLOAD_DIR=/home/agent-admin/agent-app/upload_files
AGENT_KEY_PATH=/home/agent-admin/agent-app/api_keys
AGENT_LOG_DIR=/var/log/agent-app
```

Agent는 `agent-admin` 계정으로 실행하였으며 Root 계정으로 실행하지 않았습니다.

Agent 실행 시 다음 Boot Sequence를 확인 했습니다.

```text
[1/5] Checking User Account               [OK]
[2/5] Verifying Environment Variables     [OK]
[3/5] Checking Required Files             [OK]
[4/5] Checking Port Availability          [OK]
[5/5] Verifying Log Permission            [OK]

All Boot Checks Passed!
Agent READY
```

Agent 실행 후 TCP `15034` 포트에서 LISTEN 상태가 되는 것을 확인 했습니다.

## 5. monitor.sh

`monitor.sh`를 사용하여 Agent의 상태를 자동으로 점검하도록 구성 했습니다.

파일 위치:

```text
/home/agent-admin/agent-app/bin/monitor.sh
```

주요 점검 항목:

* Agent 프로세스 실행 여부
* TCP `15034` 포트 LISTEN 여부
* UFW 활성화 여부
* CPU 사용량
* 메모리 사용량
* 루트 디스크 사용량

다음 기준을 초과하면 경고를 출력하도록 구성 했습니다.

```text
CPU > 20%
MEM > 10%
DISK_USED > 80%
```

Agent가 실행되지 않거나 `15034` 포트가 LISTEN 상태가 아닌 경우에는 `[FAIL]`을 출력하고 종료하도록 구성 했습니다.

## 6. 로그 기록

모니터링 결과는 다음 파일에 기록됩니다.

```text
/var/log/agent-app/monitor.log
```

로그에는 다음 정보가 기록됩니다.

```text
시간
PID
CPU 사용량
메모리 사용량
디스크 사용량
```

예시:

```text
[2026-09-18 10:52:01] PID:373 CPU:0% MEM:16.5424% DISK_USED:1%
```

로그 파일이 일정 크기 이상 증가할 경우 기존 로그를 순환 저장하도록 구성 했습니다.

## 7. Cron 자동 실행

`agent-admin` 계정의 crontab에 `monitor.sh`를 등록 했습니다.

```text
* * * * * /home/agent-admin/agent-app/bin/monitor.sh
```

1분마다 `monitor.sh`가 자동 실행되며, 실제로 `monitor.log`에 약 1분 간격으로 새로운 로그가 추가되는 것을 확인 했습니다.

## 8. 실행 확인

`monitor.sh` 실행 결과 다음과 같은 상태를 확인 했습니다.

```text
[OK] Agent application is running
[OK] TCP port 15034 is LISTEN
[OK] UFW is active
CPU: 0~1% 정도
MEM: 약 16~19%
DISK_USED: 1%
```

메모리 사용량은 설정한 경고 기준인 10%를 초과하여 `[WARNING]` 메시지가 출력되는 것도 확인 했습니다.

## 9. Mac 환경에서의 확인

현재 개발 환경은 Mac이며, Linux 전용 설정인 SSH 및 일부 계정/방화벽 관련 점검은 Linux Docker 환경에서 수행 헸습니다.

Mac에서 Linux 전용 항목을 실행할 경우 환경이 Linux가 아니므로 `SKIP` 처리되도록 구성 햇습니다다.

## 10. 사용 파일

```text
main.py
monitor.sh
README.md
```

`main.py`는 Agent 상태 점검 프로그램이며, `monitor.sh`는 Agent의 상태를 주기적으로 확인하고 결과를 로그로 기록하는 자동화 스크립트 입니다.
