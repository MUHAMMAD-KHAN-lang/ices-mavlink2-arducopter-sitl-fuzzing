import json
import random
import socket
import time
from pathlib import Path

from pymavlink.dialects.v20 import common as mavlink2

SITL_IP = "192.168.18.6"
SITL_PORT = 5760
MONITOR_IP = "192.168.18.6"
MONITOR_PORT = 9001
MSG_ID = 0
SYSTEM_ID = 255
COMPONENT_ID = 0
RANDOM_SEED = 20260918
PROCESS_DELAY = 0.5
INTER_TEST_DELAY = 0.2
LOG_DIR = Path("Fuzz_logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "case7_results.txt"
MESSAGE_MAP = mavlink2.mavlink_map
CRC_EXTRA = MESSAGE_MAP[MSG_ID].crc_extra


def crc_accumulate(data, crc):
    tmp = data ^ (crc & 0xFF)
    tmp ^= (tmp << 4) & 0xFF
    crc = (crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)
    return crc & 0xFFFF


def mavlink_crc(buffer, crc_extra):
    crc = 0xFFFF
    for byte in buffer:
        crc = crc_accumulate(byte, crc)
    return crc_accumulate(crc_extra, crc)


def build_packet(actual_payload, declared_length, sequence):
    actual_length = len(actual_payload)
    if not 0 <= declared_length <= 255:
        raise ValueError("MAVLink 2 declared length must be 0..255")
    if not 1 <= actual_length <= 255:
        raise ValueError("Actual payload length must be 1..255")
    if actual_length == declared_length:
        raise ValueError("Case 7 requires a length mismatch")

    header = bytes([
        declared_length,
        0,
        0,
        sequence & 0xFF,
        SYSTEM_ID,
        COMPONENT_ID,
        MSG_ID & 0xFF,
        (MSG_ID >> 8) & 0xFF,
        (MSG_ID >> 16) & 0xFF,
    ])
    crc = mavlink_crc(header + actual_payload, CRC_EXTRA)
    return bytes([0xFD]) + header + actual_payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])


def send_one_test(packet):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(5)
        print("[DEBUG] Connecting to SITL...")
        sock.connect((SITL_IP, SITL_PORT))
        print("[DEBUG] TCP CONNECT SUCCESS")
        print(f"[DEBUG] Sending {len(packet)} bytes...")
        sock.sendall(packet)
        print("[DEBUG] SEND SUCCESS")
        time.sleep(PROCESS_DELAY)
        try:
            sock.shutdown(socket.SHUT_WR)
        except OSError:
            pass
        sock.close()
        return "SUCCESS"
    except socket.timeout:
        try:
            sock.close()
        except OSError:
            pass
        return "FAILED: SOCKET_TIMEOUT"
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
        return {"SITL_PROCESS": "UNKNOWN", "PORT_5760": "UNKNOWN", "RESULT": f"MONITOR_ERROR: {exc}"}


def main():
    rng = random.Random(RANDOM_SEED)
    tests = []
    for actual_length in range(1, 256):
        tests.append(("7A_MINUS_ONE", actual_length, actual_length - 1))
    for actual_length in range(1, 255):
        tests.append(("7B_PLUS_ONE", actual_length, actual_length + 1))

    sequence = 0
    print(f"[+] Case 7: {len(tests)} tests")

    with open(LOG_FILE, "w", encoding="utf-8") as log:
        log.write("MAVLink Test Case 7\n===================\n")
        log.write("SUBCASE_7A: declared = actual - 1\n")
        log.write("SUBCASE_7B: declared = actual + 1\n")
        log.write(f"RANDOM_SEED: {RANDOM_SEED}\n")

        for test_id, (subcase, actual_length, declared_length) in enumerate(tests, start=1):
            payload = bytes(rng.getrandbits(8) for _ in range(actual_length))
            packet = build_packet(payload, declared_length, sequence)
            tcp_status = send_one_test(packet)
            status = get_sitl_status()

            log.write(f"TEST_ID: {test_id}\nSUBCASE: {subcase}\nMSG_ID: {MSG_ID}\n")
            log.write(f"DECLARED_LENGTH: {declared_length}\nACTUAL_LENGTH: {actual_length}\n")
            log.write(f"LENGTH_DELTA: {declared_length - actual_length}\nSEQUENCE: {sequence}\n")
            log.write(f"PAYLOAD_HEX: {payload.hex(' ')}\nFRAME_HEX: {packet.hex(' ')}\n")
            log.write(f"TCP_SEND: {tcp_status}\nSITL_PROCESS: {status['SITL_PROCESS']}\n")
            log.write(f"PORT_5760: {status['PORT_5760']}\nRESULT: {status['RESULT']}\n\n")

            print(
                f"[TX] Test {test_id:03d} | {subcase} | Declared {declared_length:03d} | "
                f"Actual {actual_length:03d} | TCP {tcp_status} | SITL {status['SITL_PROCESS']} | "
                f"Port {status['PORT_5760']} | {status['RESULT']}"
            )

            if status["SITL_PROCESS"] == "NOT_RUNNING":
                print(f"[!!!] POSSIBLE SITL CRASH at test {test_id}")
                return

            sequence = (sequence + 1) & 0xFF
            time.sleep(INTER_TEST_DELAY)

    print(f"CASE 7 COMPLETED: {len(tests)}/{len(tests)}")


if __name__ == "__main__":
    main()
