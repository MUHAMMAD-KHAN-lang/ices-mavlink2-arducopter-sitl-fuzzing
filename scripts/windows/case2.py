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

START_MSG_ID = 0
END_MSG_ID = 255
START_PAYLOAD_LENGTH = 1
END_PAYLOAD_LENGTH = 255
SYSTEM_ID = 255
COMPONENT_ID = 0
START_SEQUENCE = 0
RANDOM_SEED = 20260918
PROCESS_DELAY = 0.1
SOCKET_TIMEOUT = 5

LOG_DIR = Path("Fuzz_logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "case2_results.txt"
MESSAGE_MAP = mavlink2.mavlink_map


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


def build_packet(msg_id, payload, sequence):
    header = bytes([
        len(payload),
        0,
        0,
        sequence & 0xFF,
        SYSTEM_ID & 0xFF,
        COMPONENT_ID & 0xFF,
        msg_id & 0xFF,
        (msg_id >> 8) & 0xFF,
        (msg_id >> 16) & 0xFF,
    ])
    crc_extra = MESSAGE_MAP[msg_id].crc_extra if msg_id in MESSAGE_MAP else 0
    crc = mavlink_crc(header + payload, crc_extra)
    return bytes([0xFD]) + header + payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])


def send_one_test(packet):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(SOCKET_TIMEOUT)
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
        sock.settimeout(SOCKET_TIMEOUT)
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
    rng = random.Random(RANDOM_SEED)
    sequence = START_SEQUENCE
    total_tests = (END_MSG_ID - START_MSG_ID + 1) * (END_PAYLOAD_LENGTH - START_PAYLOAD_LENGTH + 1)
    test_id = 0

    print("========================================")
    print("MAVLink Test Case 2")
    print("========================================")
    print(f"SITL            : {SITL_IP}:{SITL_PORT}")
    print(f"Message IDs     : {START_MSG_ID} -> {END_MSG_ID}")
    print(f"Payload lengths : {START_PAYLOAD_LENGTH} -> {END_PAYLOAD_LENGTH}")
    print(f"Total tests     : {total_tests}")
    print(f"Random seed     : {RANDOM_SEED}")
    print("Mode            : ONE TCP CONNECTION PER TEST")
    print("========================================")

    with open(LOG_FILE, "w", encoding="utf-8") as log:
        log.write("MAVLink Test Case 2\n===================\n")
        log.write(f"RANDOM_SEED: {RANDOM_SEED}\n")
        log.write(f"SYSTEM_ID: {SYSTEM_ID}\nCOMPONENT_ID: {COMPONENT_ID}\n")
        log.write("MODE: ONE TCP CONNECTION PER TEST\n\n")

        for msg_id in range(START_MSG_ID, END_MSG_ID + 1):
            for payload_length in range(START_PAYLOAD_LENGTH, END_PAYLOAD_LENGTH + 1):
                test_id += 1
                payload = bytes(rng.getrandbits(8) for _ in range(payload_length))
                packet = build_packet(msg_id, payload, sequence)
                tcp_status = send_one_test(packet)
                sitl_status = get_sitl_status()

                log.write(f"TEST_ID: {test_id}\n")
                log.write(f"MSG_ID: {msg_id}\n")
                log.write(f"PAYLOAD_LENGTH: {payload_length}\n")
                log.write(f"SEQUENCE: {sequence}\n")
                log.write(f"PAYLOAD_HEX: {payload.hex(' ')}\n")
                log.write(f"FRAME_HEX: {packet.hex(' ')}\n")
                log.write(f"TCP_SEND: {tcp_status}\n")
                log.write(f"SITL_PROCESS: {sitl_status['SITL_PROCESS']}\n")
                log.write(f"PORT_5760: {sitl_status['PORT_5760']}\n")
                log.write(f"RESULT: {sitl_status['RESULT']}\n\n")

                print(
                    f"[TX] Test {test_id:05d} | MsgID {msg_id:03d} | Len {payload_length:03d} | "
                    f"TCP {tcp_status} | SITL {sitl_status['SITL_PROCESS']} | "
                    f"Port {sitl_status['PORT_5760']} | {sitl_status['RESULT']}"
                )

                if sitl_status["SITL_PROCESS"] == "NOT_RUNNING":
                    print(f"[!!!] POSSIBLE SITL CRASH at test {test_id}")
                    return

                sequence = (sequence + 1) & 0xFF

    print("\n========================================")
    print("CASE 2 COMPLETED")
    print(f"Tests executed: {test_id}")
    print(f"Expected tests: {total_tests}")
    print(f"Log: {LOG_FILE}")
    print("========================================")


if __name__ == "__main__":
    main()
