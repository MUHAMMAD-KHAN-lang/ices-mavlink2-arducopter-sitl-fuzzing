import socket
from pathlib import Path
import json
import time

from pymavlink.dialects.v20 import common as mavlink2


# ============================================================
# CONFIGURATION
# ============================================================

SITL_IP = "192.168.18.6"
SITL_PORT = 5760

MONITOR_IP = "192.168.18.6"
MONITOR_PORT = 9001

START_MSG_ID = 0
END_MSG_ID = 255

SYSTEM_ID = 255
COMPONENT_ID = 0

START_SEQUENCE = 0

# Give SITL time to process each packet
PROCESS_DELAY = 0.1

LOG_DIR = Path("Fuzz_logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "case3_results.txt"


# ============================================================
# MAVLink CRC
# ============================================================

def crc_accumulate(data, crc):

    tmp = data ^ (crc & 0xFF)

    tmp ^= (tmp << 4) & 0xFF

    crc = (
        (crc >> 8)
        ^ (tmp << 8)
        ^ (tmp << 3)
        ^ (tmp >> 4)
    )

    return crc & 0xFFFF


def mavlink_crc(buffer, crc_extra):

    crc = 0xFFFF

    for byte in buffer:
        crc = crc_accumulate(byte, crc)

    crc = crc_accumulate(crc_extra, crc)

    return crc


# ============================================================
# MAVLink MESSAGE MAP
# ============================================================

MESSAGE_MAP = mavlink2.mavlink_map


# ============================================================
# BUILD MAVLink 2 ZERO-PAYLOAD PACKET
# ============================================================

def build_packet(msg_id, sequence):

    # --------------------------------------------------------
    # CASE 3:
    # Payload is exactly zero bytes
    # --------------------------------------------------------

    payload = b""

    # --------------------------------------------------------
    # MAVLink 2 header
    # --------------------------------------------------------

    header = bytes([
        0,                          # payload length
        0,                          # incompatibility flags
        0,                          # compatibility flags
        sequence & 0xFF,             # sequence
        SYSTEM_ID & 0xFF,            # system ID
        COMPONENT_ID & 0xFF,         # component ID

        # 24-bit message ID
        msg_id & 0xFF,
        (msg_id >> 8) & 0xFF,
        (msg_id >> 16) & 0xFF,
    ])

    # --------------------------------------------------------
    # CRC_EXTRA
    # --------------------------------------------------------

    if msg_id in MESSAGE_MAP:

        crc_extra = MESSAGE_MAP[msg_id].crc_extra

    else:

        crc_extra = 0

    # --------------------------------------------------------
    # Calculate CRC
    # --------------------------------------------------------

    crc = mavlink_crc(
        header + payload,
        crc_extra
    )

    # MAVLink transmits CRC low byte first
    crc_bytes = bytes([
        crc & 0xFF,
        (crc >> 8) & 0xFF
    ])

    # --------------------------------------------------------
    # Complete MAVLink 2 packet
    # --------------------------------------------------------

    packet = (
        bytes([0xFD])
        + header
        + payload
        + crc_bytes
    )

    return packet


# ============================================================
# GET SITL STATUS
# ============================================================

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

        try:
            sock.close()
        except Exception:
            pass

        return {
            "SITL_PROCESS": "UNKNOWN",
            "PORT_5760": "UNKNOWN",
            "RESULT": f"MONITOR_ERROR: {e}"
        }


# ============================================================
# MAIN
# ============================================================

sequence = START_SEQUENCE
test_id = 0

total_tests = (
    END_MSG_ID
    - START_MSG_ID
    + 1
)


print("========================================")
print("MAVLink Test Case 3")
print("========================================")
print(
    f"SITL            : "
    f"{SITL_IP}:{SITL_PORT}"
)
print(
    f"Message IDs     : "
    f"{START_MSG_ID} -> {END_MSG_ID}"
)
print("Payload length  : 0 bytes")
print(f"Total tests     : {total_tests}")
print("Mode            : ONE PERSISTENT TCP CONNECTION")
print(f"Delay           : {PROCESS_DELAY} seconds")
print("========================================")


# ============================================================
# CONNECT ONCE
# ============================================================

sock = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

sock.settimeout(5)

print("[DEBUG] Connecting to SITL...")

sock.connect(
    (SITL_IP, SITL_PORT)
)

print("[DEBUG] TCP CONNECT SUCCESS")


# ============================================================
# OPEN LOG
# ============================================================

with open(
    LOG_FILE,
    "w"
) as log:

    log.write(
        "MAVLink Test Case 3\n"
    )

    log.write(
        "===================\n"
    )

    log.write(
        f"SYSTEM_ID: {SYSTEM_ID}\n"
    )

    log.write(
        f"COMPONENT_ID: {COMPONENT_ID}\n"
    )

    log.write(
        "PAYLOAD_LENGTH: 0\n"
    )

    log.write(
        "MODE: ONE PERSISTENT TCP CONNECTION\n\n"
    )


    # ========================================================
    # TEST LOOP
    # ========================================================

    for msg_id in range(
        START_MSG_ID,
        END_MSG_ID + 1
    ):

        test_id += 1

        # ----------------------------------------------------
        # Build zero-payload packet
        # ----------------------------------------------------

        packet = build_packet(
            msg_id,
            sequence
        )


        # ----------------------------------------------------
        # Send packet
        # ----------------------------------------------------

        try:

            print(
                f"[DEBUG] Test {test_id:03d}: "
                f"Sending {len(packet)} bytes..."
            )

            sock.sendall(packet)

            tcp_status = "SUCCESS"

            print(
                "[DEBUG] SEND SUCCESS"
            )

        except Exception as e:

            tcp_status = (
                f"FAILED: "
                f"{type(e).__name__}: {e}"
            )

            print(
                f"[DEBUG] SEND FAILED: {e}"
            )


        # ----------------------------------------------------
        # Give SITL time to process
        # ----------------------------------------------------

        time.sleep(
            PROCESS_DELAY
        )


        # ----------------------------------------------------
        # Check SITL
        # ----------------------------------------------------

        sitl_status = get_sitl_status()


        # ----------------------------------------------------
        # Write log
        # ----------------------------------------------------

        log.write(
            f"TEST_ID: {test_id}\n"
        )

        log.write(
            f"MSG_ID: {msg_id}\n"
        )

        log.write(
            "PAYLOAD_LENGTH: 0\n"
        )

        log.write(
            f"SEQUENCE: {sequence}\n"
        )

        log.write(
            "PAYLOAD_HEX: <EMPTY>\n"
        )

        log.write(
            f"FRAME_HEX: "
            f"{packet.hex(' ')}\n"
        )

        log.write(
            f"TCP_SEND: "
            f"{tcp_status}\n"
        )

        log.write(
            f"SITL_PROCESS: "
            f"{sitl_status['SITL_PROCESS']}\n"
        )

        log.write(
            f"PORT_5760: "
            f"{sitl_status['PORT_5760']}\n"
        )

        log.write(
            f"RESULT: "
            f"{sitl_status['RESULT']}\n"
        )

        log.write("\n")


        # ----------------------------------------------------
        # Terminal result
        # ----------------------------------------------------

        print(
            f"[TX] Test {test_id:03d} | "
            f"MsgID {msg_id:03d} | "
            f"Len 000 | "
            f"TCP {tcp_status} | "
            f"SITL "
            f"{sitl_status['SITL_PROCESS']} | "
            f"Port "
            f"{sitl_status['PORT_5760']} | "
            f"{sitl_status['RESULT']}"
        )


        # ----------------------------------------------------
        # Stop if SITL disappeared
        # ----------------------------------------------------

        if (
            sitl_status["SITL_PROCESS"]
            == "NOT_RUNNING"
        ):

            print(
                "\n[!!!] POSSIBLE SITL CRASH"
            )

            print(
                f"[!!!] Test ID: "
                f"{test_id}"
            )

            print(
                f"[!!!] Message ID: "
                f"{msg_id}"
            )

            break


        # ----------------------------------------------------
        # Next sequence number
        # ----------------------------------------------------

        sequence = (
            sequence + 1
        ) & 0xFF


# ============================================================
# CLOSE CONNECTION
# ============================================================

sock.close()


print("\n========================================")
print("CASE 3 COMPLETED")
print(
    f"Tests executed: {test_id}"
)
print(
    f"Expected tests: {total_tests}"
)
print(
    f"Log: {LOG_FILE}"
)
print("========================================")