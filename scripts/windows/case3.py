import json
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
SYSTEM_ID = 255
COMPONENT_ID = 0
START_SEQUENCE = 0
PROCESS_DELAY = 0.1
LOG_DIR = Path("Fuzz_logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "case3_results.txt"
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


def build_packet(msg_id, sequence):
    payload = b""
    header = bytes([0, 0, 0, sequence & 0xFF, SYSTEM_ID, COMPONENT_ID,
                    msg_id & 0xFF, (msg_id >> 8) & 0xFF, (msg_id >> 16) & 0xFF])
    crc_extra = MESSAGE_MAP[msg_id].crc_extra if msg_id in MESSAGE_MAP else 0
    crc = mavlink_crc(header, crc_extra)
    return bytes([0xFD]) + header + bytes([crc & 0xFF, (crc >> 8) & 0xFF])


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
    sequence = START_SEQUENCE
    test_id = 0
    total_tests = END_MSG_ID - START_MSG_ID + 1

    print(f"[+] MAVLink Test Case 3 | {total_tests} tests")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    print("[DEBUG] Connecting to SITL...")
    sock.connect((SITL_IP, SITL_PORT))
    print("[DEBUG] TCP CONNECT SUCCESS")

    with open(LOG_FILE, "w", encoding="utf-8") as log:
        log.write("MAVLink Test Case 3\n===================\n")
        log.write("PAYLOAD_LENGTH: 0\nMODE: ONE PERSISTENT TCP CONNECTION\n\n")

        for msg_id in range(START_MSG_ID, END_MSG_ID + 1):
            test_id += 1
            packet = build_packet(msg_id, sequence)
            try:
                print(f"[DEBUG] Test {test_id:03d}: Sending {len(packet)} bytes...")
                sock.sendall(packet)
                tcp_status = "SUCCESS"
                print("[DEBUG] SEND SUCCESS")
            except Exception as exc:
                tcp_status = f"FAILED: {type(exc).__name__}: {exc}"
                print(f"[DEBUG] SEND FAILED: {exc}")

            time.sleep(PROCESS_DELAY)
            sitl_status = get_sitl_status()

            log.write(f"TEST_ID: {test_id}\nMSG_ID: {msg_id}\nPAYLOAD_LENGTH: 0\n")
            log.write(f"SEQUENCE: {sequence}\nPAYLOAD_HEX: <EMPTY>\nFRAME_HEX: {packet.hex(' ')}\n")
            log.write(f"TCP_SEND: {tcp_status}\nSITL_PROCESS: {sitl_status['SITL_PROCESS']}\n")
            log.write(f"PORT_5760: {sitl_status['PORT_5760']}\nRESULT: {sitl_status['RESULT']}\n\n")

            print(f"[TX] Test {test_id:03d} | MsgID {msg_id:03d} | Len 000 | TCP {tcp_status} | SITL {sitl_status['SITL_PROCESS']} | Port {sitl_status['PORT_5760']} | {sitl_status['RESULT']}")

            if sitl_status["SITL_PROCESS"] == "NOT_RUNNING":
                print(f"[!!!] POSSIBLE SITL CRASH at test {test_id}")
                break
            sequence = (sequence + 1) & 0xFF

    sock.close()
    print(f"CASE 3 COMPLETED: {test_id}/{total_tests}")


if __name__ == "__main__":
    main()
