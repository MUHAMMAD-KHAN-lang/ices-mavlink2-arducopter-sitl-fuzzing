import random
import socket
from pathlib import Path
import json
import time


# ==========================================
# SITL CONFIGURATION
# ==========================================

SITL_IP = "192.168.18.6"
SITL_PORT = 5760

MONITOR_IP = "192.168.18.6"
MONITOR_PORT = 9001


# ==========================================
# FUZZING CONFIGURATION
# ==========================================

NUMBER_OF_TESTS = 100

MIN_LENGTH = 1
MAX_LENGTH = 1000


# ==========================================
# LOG DIRECTORY
# ==========================================

LOG_DIR = Path("Fuzz_logs")
LOG_DIR.mkdir(exist_ok=True)


# ==========================================
# FUNCTION: SEND RANDOM DATA
# ==========================================

def send_test_case(data):

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    try:
        sock.settimeout(5)

        sock.connect((SITL_IP, SITL_PORT))

        sock.sendall(data)

        sock.close()

        return "SUCCESS"

    except Exception as e:

        sock.close()

        print(f"[!] Send error: {e}")

        return f"FAILED: {e}"


# ==========================================
# FUNCTION: ASK UBUNTU MONITOR FOR STATUS
# ==========================================

def get_sitl_status():

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    try:

        sock.settimeout(5)

        sock.connect(
            (MONITOR_IP, MONITOR_PORT)
        )

        response = sock.recv(4096)

        sock.close()

        return json.loads(
            response.decode()
        )

    except Exception as e:

        sock.close()

        return {
            "SITL_PROCESS": "UNKNOWN",
            "PORT_5760": "UNKNOWN",
            "RESULT": f"MONITOR_ERROR: {e}"
        }


# ==========================================
# MAIN FUZZING LOOP
# ==========================================

print(
    f"[+] Starting Test Case 1"
)

print(
    f"[+] SITL: {SITL_IP}:{SITL_PORT}"
)

print(
    f"[+] Tests: {NUMBER_OF_TESTS}"
)


for test_id in range(
    1,
    NUMBER_OF_TESTS + 1
):

    # --------------------------------------
    # Generate random length
    # --------------------------------------

    length = random.randint(
        MIN_LENGTH,
        MAX_LENGTH
    )


    # --------------------------------------
    # Generate completely random bytes
    # --------------------------------------

    data = bytes(
        random.getrandbits(8)
        for _ in range(length)
    )


    # --------------------------------------
    # Send data
    # --------------------------------------

    send_status = send_test_case(data)


    # Give SITL a short moment to react
    time.sleep(0.1)


    # --------------------------------------
    # Check SITL
    # --------------------------------------

    sitl_status = get_sitl_status()


    # --------------------------------------
    # Save readable test case
    # --------------------------------------

    filename = (
        LOG_DIR /
        f"test_{test_id:06d}.txt"
    )


    with open(
        filename,
        "w"
    ) as f:

        f.write(
            f"TEST_ID: {test_id}\n"
        )

        f.write(
            f"LENGTH: {length}\n"
        )

        f.write(
            f"DATA_HEX: {data.hex(' ')}\n"
        )

        f.write("\n")

        f.write(
            f"TCP_SEND: {send_status}\n"
        )

        f.write(
            f"SITL_PROCESS: "
            f"{sitl_status['SITL_PROCESS']}\n"
        )

        f.write(
            f"PORT_5760: "
            f"{sitl_status['PORT_5760']}\n"
        )

        f.write(
            f"RESULT: "
            f"{sitl_status['RESULT']}\n"
        )


    # --------------------------------------
    # Display result
    # --------------------------------------

    print(
        f"[TX] Test {test_id:03d} | "
        f"Length: {length:4d} | "
        f"TCP: {send_status} | "
        f"SITL: "
        f"{sitl_status['SITL_PROCESS']} | "
        f"Port: "
        f"{sitl_status['PORT_5760']} | "
        f"{sitl_status['RESULT']}"
    )


    # Stop immediately if SITL disappeared
    if (
        sitl_status["SITL_PROCESS"]
        == "NOT_RUNNING"
    ):

        print(
            "[!!!] POSSIBLE SITL CRASH"
        )

        print(
            f"[!!!] Triggering test: "
            f"{test_id}"
        )

        break


print(
    "[+] Test Case 1 finished"
)