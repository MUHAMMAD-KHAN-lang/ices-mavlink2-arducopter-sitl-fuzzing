import json
import socket
import subprocess

MONITOR_IP = "192.168.18.6"
MONITOR_PORT = 9001
SITL_PORT = 5760


def check_sitl_process():
    result = subprocess.run(
        ["pgrep", "-x", "arducopter"],
        capture_output=True,
        text=True,
    )
    return "RUNNING" if result.returncode == 0 else "NOT_RUNNING"


def check_sitl_port():
    result = subprocess.run(
        ["ss", "-ltn"],
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        if f":{SITL_PORT} " in line:
            return "LISTENING"
    return "CLOSED"


def get_status():
    process_status = check_sitl_process()
    port_status = check_sitl_port()

    if process_status == "RUNNING" and port_status == "LISTENING":
        result = "NO_CRASH_DETECTED"
    elif process_status != "RUNNING":
        result = "POSSIBLE_CRASH"
    else:
        result = "SITL_NOT_LISTENING"

    return {
        "SITL_PROCESS": process_status,
        "PORT_5760": port_status,
        "RESULT": result,
    }


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((MONITOR_IP, MONITOR_PORT))
    server.listen(5)

    print(f"[+] SITL monitor listening on {MONITOR_IP}:{MONITOR_PORT}")

    while True:
        client, _address = server.accept()
        try:
            response = json.dumps(get_status()).encode()
            client.sendall(response)
        finally:
            client.close()


if __name__ == "__main__":
    main()
