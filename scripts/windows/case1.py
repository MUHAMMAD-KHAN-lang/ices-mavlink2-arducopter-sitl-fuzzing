import random
import socket
from pathlib import Path
import json
import time

SITL_IP = "192.168.18.6"
SITL_PORT = 5760
MONITOR_IP = "192.168.18.6"
MONITOR_PORT = 9001

NUMBER_OF_TESTS = 100
MIN_LENGTH = 1
MAX_LENGTH = 1000
PROCESS_DELAY = 0.1

LOG_DIR = Path("Fuzz_logs")
LOG_DIR.mkdir(exist_ok=True)


def send_test_case(data):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(5)
        sock.connect((SITL_IP, SITL_PORT))
        sock.sendall(data)
        time.sleep(PROCESS_DELAY)
        sock.close()
        return "SUCCESS"
    except Exception as exc:
        try:
            sock.close()
        except OSError:
            pass
        return f"FAILED: {type(exc).__name__}: {exc}"


def get_sitl_status():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(5)
        sock.connect((MONITOR_IP, MONITOR_PORT))
        response = sock.recv(4096)
        sock.close()
        return json.loads(response.decode())
    except Exception as exc:
        try:
            sock.close()
        except OSError:
            pass
        return {
            "SITL_PROCESS": "UNKNOWN",
            "PORT_5760": "UNKNOWN",
            "RESULT": f"MONITOR_ERROR: {exc}",
        }


def main():
    for test_id in range(1, NUMBER_OF_TESTS + 1):
        length = random.randint(MIN_LENGTH, MAX_LENGTH)
        data = bytes(random.getrandbits(8) for _ in range(length))

        tcp_status = send_test_case(data)
        sitl_status = get_sitl_status()

        filename = LOG_DIR / f"case1_test_{test_id:06d}.txt"
        with open(filename, "w", encoding="utf-8") as log:
            log.write(f"TEST_ID: {test_id}\n")
            log.write(f"LENGTH: {length}\n")
            log.write(f"DATA_HEX: {data.hex(' ')}\n\n")
            log.write(f"TCP_SEND: {tcp_status}\n")
            log.write(f"SITL_PROCESS: {sitl_status['SITL_PROCESS']}\n")
            log.write(f"PORT_5760: {sitl_status['PORT_5760']}\n")
            log.write(f"RESULT: {sitl_status['RESULT']}\n")

        print(
            f"[TX] Test {test_id:03d} | Length {length:4d} | "
            f"TCP {tcp_status} | SITL {sitl_status['SITL_PROCESS']} | "
            f"Port {sitl_status['PORT_5760']} | {sitl_status['RESULT']}"
        )

        if sitl_status["SITL_PROCESS"] == "NOT_RUNNING":
            print(f"[!!!] POSSIBLE SITL CRASH at test {test_id}")
            break


if __name__ == "__main__":
    main()
