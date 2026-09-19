import json
import socket
import time
from pathlib import Path

from pymavlink.dialects.v20 import common as mavlink2

SITL_IP = "192.168.18.6"
SITL_PORT = 5760
MONITOR_IP = "192.168.18.6"
MONITOR_PORT = 9001
MSG_ID = 0
START_PAYLOAD_LENGTH = 1
END_PAYLOAD_LENGTH = 255
SYSTEM_ID = 255
COMPONENT_ID = 0
PROCESS_DELAY = 0.1
LOG_DIR = Path("Fuzz_logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "case4_results.txt"
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


def build_packet(payload, sequence):
    header = bytes([len(payload), 0, 0, sequence & 0xFF, SYSTEM_ID, COMPONENT_ID,
                    MSG_ID & 0xFF, (MSG_ID >> 8) & 0xFF, (MSG_ID >> 16) & 0xFF])
    crc_extra = MESSAGE_MAP[MSG_ID].crc_extra
    crc = mavlink_crc(header + payload, crc_extra)
    return bytes([0xFD]) + header + payload + bytes([crc & 0xFF, (crc >> 8) & 0xFF])


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
    sequence = 0
    total_tests = END_PAYLOAD_LENGTH - START_PAYLOAD_LENGTH + 1
    test_id = 0

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    print("[DEBUG] Connecting to SITL...")
    sock.connect((SITL_IP, SITL_PORT))
    print("[DEBUG] TCP CONNECT SUCCESS")

    with open(LOG_FILE, "w", encoding="utf-8") as log:
        log.write("MAVLink Test Case 4\n===================\nMSG_ID: 0\nPAYLOAD_PATTERN: ALL_ZERO\n")
        for payload_length in range(START_PAYLOAD_LENGTH, END_PAYLOAD_LENGTH + 1):
            test_id += 1
            payload = bytes([0x00] * payload_length)
            packet = build_packet(payload, sequence)
            try:
                print(f"[DEBUG] Test {test_id:03d}: Sending {len(packet)} bytes...")
                sock.sendall(packet)
                tcp_status = "SUCCESS"
                print("[DEBUG] SEND SUCCESS")
            except Exception as exc:
                tcp_status = f"FAILED: {type(exc).__name__}: {exc}"
                print(f"[DEBUG] SEND FAILED: {exc}")

            time.sleep(PROCESS_DELAY)
            status = get_sitl_status()
            log.write(f"TEST_ID: {test_id}\nMSG_ID: 0\nPAYLOAD_LENGTH: {payload_length}\nSEQUENCE: {sequence}\nPAYLOAD_HEX: {payload.hex(' ')}\nFRAME_HEX: {packet.hex(' ')}\nTCP_SEND: {tcp_status}\nSITL_PROCESS: {status['SITL_PROCESS']}\nPORT_5760: {status['PORT_5760']}\nRESULT: {status['RESULT']}\n\n")
            print(f"[TX] Test {test_id:03d} | MsgID 000 | Len {payload_length:03d} | TCP {tcp_status} | SITL {status['SITL_PROCESS']} | Port {status['PORT_5760']} | {status['RESULT']}")
            if status["SITL_PROCESS"] == "NOT_RUNNING":
                print(f"[!!!] POSSIBLE SITL CRASH at test {test_id}")
                break
            sequence = (sequence + 1) & 0xFF

    sock.close()
    print(f"CASE 4 COMPLETED: {test_id}/{total_tests}")


if __name__ == "__main__":
    main()
