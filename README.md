# 컴퓨터가 알아서 자기 상태를 점검하게 만들기

Linux 환경에서 Agent 실행에 필요한 보안, 계정, 권한, 네트워크 환경을 구성하고 `monitor.sh`를 통해 Agent의 실행 상태와 시스템 자원을 자동으로 점검하는 프로젝트입니다.

---

# 1. 프로젝트 개요

## 프로젝트 목표

Agent가 안정적으로 실행될 수 있도록 Linux 서버 환경을 구성하고, 주기적으로 시스템 상태를 확인하여 문제가 발생했을 때 확인할 수 있도록 하는 것을 목표로 합니다.

## 주요 구성

| 구성 요소        | 역할                 |
| ------------ | ------------------ |
| SSH          | 원격 관리용 접속 환경       |
| UFW          | 외부 접근 포트 제한        |
| agent-admin  | Agent 운영 및 관리      |
| agent-dev    | 개발 및 monitor.sh 관리 |
| agent-test   | 테스트                |
| agent-common | 사용자 간 공용 작업 권한 관리  |
| agent-core   | 운영 및 보안 관련 권한 관리   |
| Agent        | 실제 서비스 프로그램        |
| monitor.sh   | Agent 및 시스템 상태 점검  |
| cron         | monitor.sh 자동 실행   |
| monitor.log  | 점검 결과 기록           |

## 프로젝트 구조

```text
컴퓨터가 알아서 자기 상태를 점검하게 만들기/
├── README.md
└── monitor.sh
```

---

# 2. 기본 보안 및 네트워크 설정

## 2-1. SSH 설정

SSH 원격 접속 포트를 기본 포트인 22번이 아닌 `20022`번으로 변경했습니다.

또한 root 계정의 원격 로그인을 차단하여 직접적인 root 원격 접속을 제한했습니다.

| 항목          | 설정                     |
| ----------- | ---------------------- |
| SSH 포트      | `20022`                |
| Root 원격 로그인 | 비활성화                   |
| SSH 설정 파일   | `/etc/ssh/sshd_config` |
| 설정 확인       | `sshd -t`              |
| 리슨 포트 확인    | `ss -tulnp`            |

주요 설정:

```text
Port 20022
PermitRootLogin no
```

설정 변경 후 `sshd -t`를 이용하여 SSH 설정 문법에 문제가 없는지 확인하고, `ss -tulnp`를 이용하여 실제 `20022` 포트가 LISTEN 상태인지 확인했습니다.

---

## 2-2. 방화벽 설정

UFW를 사용하여 외부에서 접근할 수 있는 포트를 필요한 포트로 제한했습니다.

| 방향  |        포트 | 용도        |
| --- | --------: | --------- |
| IN  | TCP 20022 | SSH 원격 관리 |
| IN  | TCP 15034 | Agent 서비스 |
| 그 외 |         - | 기본적으로 차단  |

UFW의 기본 정책은 외부에서 들어오는 연결을 차단하고 필요한 포트만 허용하는 방식으로 구성했습니다.

```text
Default: deny incoming
Default: allow outgoing
```

### 허용 포트

```text
20022/tcp
15034/tcp
```

방화벽 상태는 다음 명령으로 확인할 수 있습니다.

```bash
ufw status
```

실제 서비스가 리슨하고 있는 포트는 다음 명령으로 확인했습니다.

```bash
ss -tulnp
```

---

## 2-3. SSH 보안의 목적과 위협 대응

SSH를 외부에 공개할 경우 반복적인 로그인 시도와 비밀번호 대입 공격과 같은 brute-force 공격의 대상이 될 수 있습니다.

따라서 다음과 같이 접근 범위를 제한했습니다.

1. SSH 포트를 `20022`로 변경
2. root 계정의 원격 로그인을 차단
3. UFW를 이용하여 필요한 포트만 허용
4. Agent와 SSH의 리슨 포트를 `ss`로 확인
5. SSH 및 시스템 로그를 통해 비정상적인 접근 시도를 확인할 수 있도록 구성

현재 프로젝트에서는 방화벽과 root 원격 로그인 제한을 통해 공격 가능한 범위를 줄이는 데 중점을 두었습니다.

---

# 3. 계정 / 그룹 / 권한 체계

계정별 역할을 분리하고 그룹을 이용하여 필요한 작업에만 접근할 수 있도록 구성했습니다.

## 3-1. 계정과 그룹

| 그룹             | 사용자                                          | 역할       | 접근 목적                   |
| -------------- | -------------------------------------------- | -------- | ----------------------- |
| `agent-common` | `agent-admin`<br>`agent-dev`<br>`agent-test` | 공용 작업 그룹 | 업로드 파일 공동 작업            |
| `agent-core`   | `agent-admin`<br>`agent-dev`                 | 핵심 운영 그룹 | API Key, 로그, 모니터링 관련 작업 |

### 사용자별 역할

| 사용자           | 소속 그룹                        | 역할                 |
| ------------- | ---------------------------- | ------------------ |
| `agent-admin` | `agent-common`, `agent-core` | Agent 운영 및 관리      |
| `agent-dev`   | `agent-common`, `agent-core` | 개발 및 monitor.sh 관리 |
| `agent-test`  | `agent-common`               | 테스트 및 공용 파일 작업     |

이와 같이 그룹을 나눈 이유는 모든 사용자에게 서버의 모든 권한을 주지 않고, 실제 업무에 필요한 범위만 접근할 수 있도록 하기 위해서입니다.

---

## 3-2. 디렉터리 권한

Agent 관련 파일은 역할에 따라 접근 범위를 분리했습니다.

| 경로                   | 소유자           | 그룹             | 접근 대상          | 목적                    |
| -------------------- | ------------- | -------------- | -------------- | --------------------- |
| `upload_files`       | `agent-admin` | `agent-common` | admin/dev/test | 공용 파일 업로드 및 관리        |
| `api_keys`           | `agent-admin` | `agent-core`   | admin/dev      | API Key 등 민감 정보 관리    |
| `/var/log/agent-app` | `agent-admin` | `agent-core`   | admin/dev      | Agent 및 monitor 로그 관리 |
| `monitor.sh`         | `agent-dev`   | `agent-core`   | admin/dev      | 모니터링 스크립트 관리          |

주요 디렉터리 구조:

```text
/home/agent-admin/agent-app/
├── agent-app-linux-arm64
├── upload_files/
├── api_keys/
└── bin/
    └── monitor.sh

/var/log/agent-app/
```

### 최소 권한을 적용한 이유

API Key나 시스템 로그는 모든 사용자가 접근할 필요가 없는 정보입니다.

따라서 공용 작업이 필요한 파일은 `agent-common` 그룹으로 관리하고, 운영 및 보안에 관련된 파일은 `agent-core` 그룹으로 제한했습니다.

이렇게 권한을 분리하면 특정 계정이 필요 이상의 파일을 수정하거나 민감한 정보를 확인하는 것을 줄일 수 있습니다.

---

# 4. Agent 실행 환경

## 4-1. 환경 변수

Agent가 사용하는 주요 환경 변수는 다음과 같이 구성했습니다.

```bash
export AGENT_HOME=/home/agent-admin/agent-app
export AGENT_PORT=15034
export AGENT_UPLOAD_DIR=$AGENT_HOME/upload_files
export AGENT_KEY_PATH=$AGENT_HOME/api_keys
export AGENT_LOG_DIR=/var/log/agent-app
```

| 환경 변수              | 값                             | 용도            |
| ------------------ | ----------------------------- | ------------- |
| `AGENT_HOME`       | `/home/agent-admin/agent-app` | Agent 작업 디렉터리 |
| `AGENT_PORT`       | `15034`                       | Agent 서비스 포트  |
| `AGENT_UPLOAD_DIR` | `upload_files`                | 업로드 파일 위치     |
| `AGENT_KEY_PATH`   | `api_keys`                    | Key 파일 위치     |
| `AGENT_LOG_DIR`    | `/var/log/agent-app`          | 로그 저장 위치      |

---

## 4-2. Agent 실행 계정

Agent는 root가 아닌 `agent-admin` 계정으로 실행합니다.

이는 서비스 프로그램이 필요 이상의 시스템 권한을 갖지 않도록 하기 위한 것입니다.

```bash
id
```

실행 계정 확인 후 Agent를 실행하면 다음과 같은 Boot Sequence가 출력됩니다.

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
...
Agent listening at port 15034
```

모든 Boot Check가 `[OK]` 상태가 된 후 `Agent READY`가 출력되고 `15034` 포트에서 서비스를 시작합니다.

---

# 5. monitor.sh

`monitor.sh`는 Agent가 정상적으로 실행되고 있는지와 서버의 기본적인 상태를 주기적으로 확인하는 모니터링 스크립트입니다.

## 5-1. 스크립트 역할

| 점검 항목      | 확인 방법         | 실패 또는 경고         |
| ---------- | ------------- | ---------------- |
| Agent 프로세스 | `pgrep`       | Agent 미실행 시 FAIL |
| Agent 포트   | `ss`          | 15034 미리슨 시 FAIL |
| UFW        | 설정 파일 확인      | 비활성 시 WARNING    |
| CPU        | `top`         | 20% 초과 시 WARNING |
| 메모리        | `free`        | 10% 초과 시 WARNING |
| 디스크        | `df`          | 80% 초과 시 WARNING |
| 로그         | `monitor.log` | 지속적으로 기록         |

---

## 5-2. Agent 프로세스 확인

```bash
pgrep -f "agent-app-linux-arm64"
```

Agent 프로세스가 실행 중이면 정상으로 판단하고, 실행 중이지 않으면 FAIL을 출력하고 종료합니다.

```text
[OK] Agent application is running
```

프로세스가 존재하지 않는 경우:

```text
[FAIL] Agent application is not running
```

프로세스 확인에 `pgrep`을 사용한 이유는 실행 중인 Agent 프로세스를 간단하게 검색할 수 있고, 프로세스가 존재하는지 여부를 스크립트에서 바로 판단할 수 있기 때문입니다.

---

## 5-3. Agent 포트 확인

```bash
ss -lnt | grep -q ':15034 '
```

Agent가 실제로 `15034` 포트를 LISTEN 상태로 사용하고 있는지 확인합니다.

```text
[OK] TCP port 15034 is LISTEN
```

프로세스는 실행 중이지만 포트가 열려 있지 않은 경우 서비스의 정상적인 통신이 불가능하므로 FAIL로 처리합니다.

### 프로세스는 실행 중인데 포트가 닫혀 있는 경우

다음과 같은 원인을 우선적으로 확인할 수 있습니다.

1. Agent가 `15034` 포트에 정상적으로 bind하지 못한 경우
2. 다른 프로세스가 해당 포트를 사용하고 있는 경우
3. Agent 실행 설정 또는 환경 변수 문제
4. 방화벽 설정 문제

따라서 `pgrep`과 `ss`를 함께 사용하여 단순히 프로세스가 존재하는 것뿐만 아니라 실제 서비스 포트까지 확인하도록 했습니다.

---

# 6. 시스템 자원 점검

## 6-1. CPU / Memory / Disk

`monitor.sh`에서는 Linux 기본 명령어를 이용하여 시스템 자원을 확인합니다.

| 항목     | 명령어    |  경고 기준 |
| ------ | ------ | -----: |
| CPU    | `top`  | 20% 초과 |
| Memory | `free` | 10% 초과 |
| Disk   | `df`   | 80% 초과 |

예시:

```text
CPU: 1.3%
MEM: 17.0678%
DISK_USED: 1%
[WARNING] Memory usage is above 10%
```

현재 기준은 과도한 시스템 사용을 조기에 확인하기 위한 단순한 점검 기준입니다.

---

## 6-2. 명령어 선택 이유

| 명령어     | 선택 이유                                 |
| ------- | ------------------------------------- |
| `pgrep` | 특정 Agent 프로세스의 실행 여부를 간단하게 확인할 수 있음   |
| `ss`    | 현재 열려 있는 네트워크 소켓과 LISTEN 포트를 확인할 수 있음 |
| `top`   | Linux 시스템의 CPU 사용량을 확인할 수 있음          |
| `free`  | 메모리 사용량을 확인할 수 있음                     |
| `df`    | 디스크 사용량을 확인할 수 있음                     |

별도의 외부 프로그램을 설치하지 않고 Linux에서 기본적으로 제공되는 명령어를 사용하여 모니터링 환경의 의존성을 줄였습니다.

---

## 6-3. 출력 형식의 한계와 대응

`top`, `free`, `df`의 출력 형식은 Linux 배포판이나 환경에 따라 일부 차이가 발생할 수 있습니다.

현재 스크립트는 해당 명령어의 일반적인 Linux 출력 형식을 기준으로 값을 추출합니다.

따라서 다른 Linux 배포판에서 출력 형식이 달라질 경우 파싱 결과가 달라질 가능성이 있습니다.

이를 방지하기 위해 실제 실행 환경에서 명령어의 출력 결과를 먼저 확인하고, 현재 환경에서 정상적으로 값을 추출할 수 있도록 `awk`와 `tr`을 사용했습니다.

---

# 7. 로그 기록

모니터링 결과는 다음 파일에 저장됩니다.

```text
/var/log/agent-app/monitor.log
```

## 로그 형식

```text
[2026-09-18 10:48:01] PID:373 CPU:0.7% MEM:18.6259% DISK_USED:1%
```

| 필드        | 의미            |
| --------- | ------------- |
| Timestamp | 점검이 실행된 시간    |
| PID       | Agent 프로세스 ID |
| CPU       | CPU 사용률       |
| MEM       | 메모리 사용률       |
| DISK_USED | 루트 파일 시스템 사용률 |

---

## 7-1. `>>`를 사용하는 이유

로그 기록에는 다음과 같이 `>>`를 사용합니다.

```bash
echo "로그 내용" >> "$LOG_FILE"
```

`>`를 사용하면 기존 파일 내용을 덮어쓰지만, `>>`는 기존 로그를 유지하면서 새로운 내용을 파일의 마지막 부분에 추가합니다.

모니터링 로그는 이전 점검 기록도 계속 확인해야 하므로 기존 내용을 유지하는 `>>` 방식을 사용했습니다.

---

# 8. 로그 용량 관리

`monitor.sh`에서는 `monitor.log`가 지나치게 커지는 것을 방지하기 위해 최대 크기를 `10MB`로 설정했습니다.

```bash
MAX_SIZE=10485760
```

로그 파일이 10MB 이상이 되면 기존 로그를 `.1`, `.2` 등의 파일로 이동하여 이전 로그를 보관하고 새로운 로그 파일을 생성합니다.

```text
monitor.log
monitor.log.1
monitor.log.2
...
monitor.log.10
```

## Script 방식의 선택 이유

이번 프로젝트에서는 별도의 `logrotate` 설정 파일을 추가하는 대신 `monitor.sh` 자체에서 로그 크기를 확인하고 순환시키는 방식을 사용했습니다.

| 방식        | 특징                                                  |
| --------- | --------------------------------------------------- |
| logrotate | Linux의 표준 로그 관리 방식으로 여러 로그 정책을 통합 관리하기 좋음           |
| 현재 방식     | 별도의 설정 파일 없이 monitor.sh 하나에서 점검과 로그 관리를 함께 수행할 수 있음 |

현재 프로젝트의 목적이 `monitor.sh`를 이용한 자동 상태 점검이므로 로그 용량 관리도 같은 스크립트 안에서 수행하도록 구성했습니다.

운영 환경이 확대될 경우에는 로그 종류와 보관 기간에 따라 `logrotate`를 사용하는 방식으로 확장할 수 있습니다.

---

# 9. Cron을 이용한 자동 실행

`monitor.sh`가 수동 실행에 그치지 않고 자동으로 실행되도록 cron을 사용했습니다.

## Crontab

```cron
* * * * * /home/agent-admin/agent-app/bin/monitor.sh
```

위 설정은 `monitor.sh`를 1분마다 실행합니다.

확인 명령:

```bash
crontab -l
```

예상 출력:

```text
* * * * * /home/agent-admin/agent-app/bin/monitor.sh
```

실제 로그에서도 약 1분 간격으로 새로운 기록이 추가되는 것을 확인했습니다.

```text
[2026-09-18 10:48:01] PID:373 CPU:0.7% MEM:18.6259% DISK_USED:1%
[2026-09-18 10:49:02] PID:373 CPU:0.7% MEM:16.3681% DISK_USED:1%
[2026-09-18 10:50:01] PID:373 CPU:0% MEM:17.8939% DISK_USED:1%
[2026-09-18 10:51:01] PID:373 CPU:0.7% MEM:17.1653% DISK_USED:1%
[2026-09-18 10:52:01] PID:373 CPU:0% MEM:16.5424% DISK_USED:1%
```

---

# 10. monitor.sh 권한 및 실행 정책

`monitor.sh`는 개발 및 운영 담당자인 `agent-dev`가 관리하고 `agent-core` 그룹에서 접근할 수 있도록 구성했습니다.

| 항목        | 설정           |
| --------- | ------------ |
| 소유자       | `agent-dev`  |
| 그룹        | `agent-core` |
| 권한        | `750`        |
| 실행 가능 사용자 | 소유자 및 그룹 사용자 |
| 기타 사용자    | 접근 제한        |

권한을 제한한 이유는 모니터링 스크립트가 시스템 프로세스, 포트, 로그 등의 정보를 확인하고 로그 파일을 수정하기 때문입니다.

모든 사용자가 스크립트를 수정할 수 있도록 하면 악의적인 명령어 삽입이나 잘못된 수정이 발생할 수 있으므로 관리 가능한 사용자로 범위를 제한했습니다.

확인 명령:

```bash
ls -l /home/agent-admin/agent-app/bin/monitor.sh
```

---

# 11. 장애 상황별 대응

monitor.sh는 모든 문제를 동일하게 처리하지 않고 문제의 종류에 따라 FAIL과 WARNING을 구분합니다.

| 상황                 | 처리      | 이유              |
| ------------------ | ------- | --------------- |
| Agent 프로세스 없음      | FAIL    | 서비스 자체가 실행되지 않음 |
| 15034 포트 LISTEN 아님 | FAIL    | 외부 서비스 통신 불가능   |
| UFW 비활성            | WARNING | 보안 설정 확인 필요     |
| CPU 20% 초과         | WARNING | 자원 사용량 확인 필요    |
| Memory 10% 초과      | WARNING | 메모리 사용량 확인 필요   |
| Disk 80% 초과        | WARNING | 저장 공간 부족 가능성    |

Agent가 실행되지 않거나 서비스 포트가 열리지 않는 경우에는 정상적인 서비스 제공이 불가능하기 때문에 즉시 확인해야 하는 상태로 판단했습니다.

CPU, 메모리, 디스크 사용량은 즉시 서비스가 중단되는 것은 아니므로 WARNING으로 구분했습니다.

---

# 12. 로그 이상 증가 대응 정책

로그가 비정상적으로 빠르게 증가할 경우 다음 순서로 확인합니다.

### 단기 대응

* 현재 `monitor.log` 크기 확인
* Agent 프로세스 상태 확인
* 반복적인 오류가 발생하고 있는지 로그 확인

### 중기 대응

* monitor.sh 실행 주기 확인
* Agent 상태 및 포트 확인
* 불필요하게 반복되는 로그가 있는지 확인
* 로그 순환이 정상적으로 동작하는지 확인

### 장기 대응

* 로그 보관 기간 검토
* 로그 발생량에 맞춰 최대 크기 조정
* 운영 환경 규모가 커질 경우 `logrotate`와 같은 별도 로그 관리 시스템 적용 검토

현재 프로젝트에서는 10MB 기준의 로그 순환 기능을 통해 로그 파일이 계속 커지는 문제를 방지했습니다.

---

# 13. 전체 점검 흐름

```text
              ┌─────────────────────┐
              │       Agent 실행     │
              │    agent-admin      │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │    Boot Sequence    │
              │       5단계 점검     │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │     Agent READY     │
              │     Port 15034      │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │      cron 실행       │
              │      1분마다          │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │     monitor.sh      │
              ├─────────────────────┤
              │ Agent 프로세스       │
              │ Port 15034          │
              │ UFW                 │
              │ CPU                 │
              │ Memory              │
              │ Disk                │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │    monitor.log      │
              │     결과 기록        │
              └─────────────────────┘
```

Agent가 `agent-admin` 계정으로 실행되면 Boot Sequence를 통해 기본 실행 환경을 확인합니다. 모든 항목이 정상적으로 확인되면 `Agent READY` 상태가 되고 `15034` 포트에서 서비스를 시작합니다.

이후 cron이 1분마다 `monitor.sh`를 실행하고, `monitor.sh`는 Agent 프로세스와 포트, 방화벽, CPU, 메모리, 디스크 상태를 점검합니다. 점검 결과는 `monitor.log`에 누적하여 기록하고, 문제가 발견되면 FAIL 또는 WARNING으로 구분하여 확인할 수 있도록 구성했습니다.
