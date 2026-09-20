import platform
import subprocess



def check_ssh_port():
    print("[SSH 포트 점검]")

    # 현재 운영체제 확인
    if platform.system() != "Linux":
        print("SKIP - Linux 환경이 아니므로 SSH 포트 점검을 수행할 수 없습니다.")
        return

    config_file = "/etc/ssh/sshd_config"

    try:
        with open(config_file, "r") as file:
            for line in file:
                line = line.strip()

                if line.startswith("Port "):
                    port = line.split()[1]

                    print(f"현재 SSH 포트: {port}")

                    if port == "20022":
                        print("PASS - SSH 포트가 20022로 설정되어 있습니다.")
                    else:
                        print("FAIL - SSH 포트가 20022가 아닙니다.")

                    return

            print("FAIL - SSH 설정에서 Port 항목을 찾을 수 없습니다.")

    except FileNotFoundError:
        print("FAIL - SSH 설정 파일을 찾을 수 없습니다.")

    except PermissionError:
        print("FAIL - SSH 설정 파일을 읽을 권한이 없습니다.")



def check_root_login():
    print("[Root 원격 로그인 점검]")

    if platform.system() != "Linux":
        print("SKIP - Linux 환경이 아니므로 Root 로그인 점검을 수행할 수 없습니다.")
        return

    config_file = "/etc/ssh/sshd_config"

    try:
        with open(config_file, "r") as file:
            for line in file:
                line = line.strip()

                if line.startswith("PermitRootLogin "):
                    value = line.split()[1]

                    print(f"현재 설정: PermitRootLogin {value}")

                    if value == "no":
                        print("PASS - Root 원격 로그인이 차단되어 있습니다.")
                    else:
                        print("FAIL - Root 원격 로그인이 허용되어 있습니다.")

                    return

            print("FAIL - PermitRootLogin 설정을 찾을 수 없습니다.")

    except FileNotFoundError:
        print("FAIL - SSH 설정 파일을 찾을 수 없습니다.")

    except PermissionError:
        print("FAIL - SSH 설정 파일을 읽을 권한이 없습니다.")


def check_ssh_listen_port():
    print("[SSH 리슨 포트 점검]")

    if platform.system() != "Linux":
        print("SKIP - Linux 환경이 아니므로 SSH 리슨 포트 점검을 수행할 수 없습니다.")
        return

    try:
        result = subprocess.run(
            ["ss", "-tulnp"],
            capture_output=True,
            text=True
        )

        if "20022" in result.stdout and "sshd" in result.stdout:
            print("PASS - SSH가 TCP 20022 포트에서 실행 중입니다.")
        else:
            print("FAIL - SSH가 TCP 20022 포트에서 실행 중이지 않습니다.")

    except FileNotFoundError:
        print("FAIL - ss 명령어를 찾을 수 없습니다.")

def check_firewall():
    print("[방화벽 점검]")

    if platform.system() != "Linux":
        print("SKIP - Linux 환경이 아니므로 방화벽 점검을 수행할 수 없습니다.")
        return

    try:
        result = subprocess.run(
            ["ufw", "status"],
            capture_output=True,
            text=True
        )

        if "Status: active" in result.stdout:
            print("PASS - UFW 방화벽이 활성화되어 있습니다.")
        else:
            print("FAIL - UFW 방화벽이 활성화되어 있지 않습니다.")

    except FileNotFoundError:
        print("FAIL - UFW가 설치되어 있지 않습니다.")

def check_allowed_ports():
    print("[방화벽 허용 포트 점검]")

    if platform.system() != "Linux":
        print("SKIP - Linux 환경이 아니므로 허용 포트 점검을 수행할 수 없습니다.")
        return

    try:
        result = subprocess.run(
            ["ufw", "status"],
            capture_output=True,
            text=True
        )

        output = result.stdout

        if "20022/tcp" in output:
            print("PASS - TCP 20022 포트가 허용되어 있습니다.")
        else:
            print("FAIL - TCP 20022 포트가 허용되어 있지 않습니다.")

        if "15034/tcp" in output:
            print("PASS - TCP 15034 포트가 허용되어 있습니다.")
        else:
            print("FAIL - TCP 15034 포트가 허용되어 있지 않습니다.")

    except FileNotFoundError:
        print("FAIL - UFW가 설치되어 있지 않습니다.")

def check_only_allowed_ports():
    print("[허용 포트 제한 점검]")

    if platform.system() != "Linux":
        print("SKIP - Linux 환경이 아니므로 허용 포트 제한 점검을 수행할 수 없습니다.")
        return

    try:
        result = subprocess.run(
            ["ufw", "status"],
            capture_output=True,
            text=True
        )

        lines = result.stdout.splitlines()
        allowed_ports = []

        for line in lines:
            if "ALLOW" in line:
                port = line.split()[0]
                allowed_ports.append(port)

        expected_ports = ["20022/tcp", "15034/tcp"]

        for port in allowed_ports:
            if port not in expected_ports:
                print(f"FAIL - 허용되지 않은 포트가 발견되었습니다: {port}")
                return

        print("PASS - 허용된 인바운드 포트가 20022/tcp와 15034/tcp로 제한되어 있습니다.")

    except FileNotFoundError:
        print("FAIL - UFW가 설치되어 있지 않습니다.")

def check_users():
    print("[사용자 계정 점검]")

    if platform.system() != "Linux":
        print("SKIP - Linux 환경이 아니므로 사용자 계정 점검을 수행할 수 없습니다.")
        return

    users = ["agent-admin", "agent-dev", "agent-test"]

    for user in users:
        result = subprocess.run(
            ["id", user],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"PASS - {user} 계정이 존재합니다.")
        else:
            print(f"FAIL - {user} 계정이 존재하지 않습니다.")

def check_groups():
    print("[그룹 점검]")

    if platform.system() != "Linux":
        print("SKIP - Linux 환경이 아니므로 그룹 점검을 수행할 수 없습니다.")
        return

    groups = ["agent-common", "agent-core"]

    for group in groups:
        result = subprocess.run(
            ["getent", "group", group],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"PASS - {group} 그룹이 존재합니다.")
        else:
            print(f"FAIL - {group} 그룹이 존재하지 않습니다.")

def check_group_members():
    print("[그룹 구성원 점검]")

    if platform.system() != "Linux":
        print("SKIP - Linux 환경이 아니므로 그룹 구성원 점검을 수행할 수 없습니다.")
        return

    expected = {
        "agent-common": ["agent-admin", "agent-dev", "agent-test"],
        "agent-core": ["agent-admin", "agent-dev"]
    }

    for group, users in expected.items():
        result = subprocess.run(
            ["getent", "group", group],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"FAIL - {group} 그룹이 존재하지 않습니다.")
            continue

        members = result.stdout.strip().split(":")[-1].split(",")

        for user in users:
            if user in members:
                print(f"PASS - {user}가 {group}에 포함되어 있습니다.")
            else:
                print(f"FAIL - {user}가 {group}에 포함되어 있지 않습니다.")


def check_directories():
    print("[디렉터리 점검]")

    if platform.system() != "Linux":
        print("SKIP - Linux 환경이 아니므로 디렉터리 점검을 수행할 수 없습니다.")
        return

    directories = [
        "/home/agent-admin/agent-app",
        "/home/agent-admin/agent-app/upload_files",
        "/home/agent-admin/agent-app/api_keys",
        "/var/log/agent-app"
    ]

    for directory in directories:
        result = subprocess.run(
            ["test", "-d", directory]
        )

        if result.returncode == 0:
            print(f"PASS - 디렉터리가 존재합니다: {directory}")
        else:
            print(f"FAIL - 디렉터리가 존재하지 않습니다: {directory}")

def check_upload_permissions():
    print("[upload_files 권한 점검]")

    if platform.system() != "Linux":
        print("SKIP - Linux 환경이 아니므로 권한 점검을 수행할 수 없습니다.")
        return

    directory = "/home/agent-admin/agent-app/upload_files"

    try:
        result = subprocess.run(
            ["stat", "-c", "%G %A", directory],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print("FAIL - 디렉터리를 확인할 수 없습니다.")
            return

        group, permissions = result.stdout.strip().split()

        print(f"그룹: {group}")
        print(f"권한: {permissions}")

        if group == "agent-common" and permissions[5:7] == "rw":
            print("PASS - agent-common 그룹에 읽기/쓰기 권한이 있습니다.")
        else:
            print("FAIL - agent-common 그룹의 읽기/쓰기 권한이 올바르지 않습니다.")

    except FileNotFoundError:
        print("FAIL - stat 명령어를 찾을 수 없습니다.")

def check_api_keys_permissions():
    print("[api_keys 권한 점검]")

    if platform.system() != "Linux":
        print("SKIP - Linux 환경이 아니므로 권한 점검을 수행할 수 없습니다.")
        return

    directory = "/home/agent-admin/agent-app/api_keys"

    try:
        result = subprocess.run(
            ["stat", "-c", "%G %A", directory],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print("FAIL - 디렉터리를 확인할 수 없습니다.")
            return

        group, permissions = result.stdout.strip().split()

        print(f"그룹: {group}")
        print(f"권한: {permissions}")

        if group == "agent-core" and permissions[5:7] == "rw":
            print("PASS - agent-core 그룹에 읽기/쓰기 권한이 있습니다.")
        else:
            print("FAIL - agent-core 그룹의 읽기/쓰기 권한이 올바르지 않습니다.")

    except FileNotFoundError:
        print("FAIL - stat 명령어를 찾을 수 없습니다.")

def check_log_permissions():
    print("[로그 디렉터리 권한 점검]")

    if platform.system() != "Linux":
        print("SKIP - Linux 환경이 아니므로 권한 점검을 수행할 수 없습니다.")
        return

    directory = "/var/log/agent-app"

    try:
        result = subprocess.run(
            ["stat", "-c", "%G %A", directory],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print("FAIL - 로그 디렉터리를 확인할 수 없습니다.")
            return

        group, permissions = result.stdout.strip().split()

        print(f"그룹: {group}")
        print(f"권한: {permissions}")

        if group == "agent-core" and permissions[5:7] == "rw":
            print("PASS - agent-core 그룹에 읽기/쓰기 권한이 있습니다.")
        else:
            print("FAIL - agent-core 그룹의 읽기/쓰기 권한이 올바르지 않습니다.")

    except FileNotFoundError:
        print("FAIL - stat 명령어를 찾을 수 없습니다.")


def check_environment_variables():
    print("[환경 변수 점검]")

    if platform.system() != "Linux":
        print("SKIP - Linux 환경이 아니므로 환경 변수 점검을 수행할 수 없습니다.")
        return

    variables = [
        "AGENT_HOME",
        "AGENT_PORT",
        "AGENT_UPLOAD_DIR",
        "AGENT_KEY_PATH",
        "AGENT_LOG_DIR"
    ]

    for variable in variables:
        value = os.environ.get(variable)

        if value:
            print(f"PASS - {variable}={value}")
        else:
            print(f"FAIL - {variable} 환경 변수가 설정되지 않았습니다.")

check_ssh_port()
check_root_login()
check_ssh_listen_port()
check_firewall()
check_allowed_ports()
check_only_allowed_ports()
check_users()
check_groups()
check_group_members()
check_directories()
check_upload_permissions()  
check_api_keys_permissions()    
check_log_permissions() 
check_environment_variables()   

