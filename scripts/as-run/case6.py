import socket
from pathlib import Path
import json
import time
import random

from pymavlink.dialects.v20 import common as mavlink2


# ============================================================
# CONFIGURATION
# ============================================================

SITL_IP = "192.168.18.6"
SITL_PORT = 5760

MONITOR_IP = "192.168.18.6"
MONITOR_PORT = 9001

# Case 6 uses one fixed message ID
MSG_ID = 0

# Payload length increases from 1 to 255
START_PAYLOAD_LENGTH = 1
END_PAYLOAD_LENGTH = 255

SYSTEM_ID = 255
COMPONENT_ID = 0

START_SEQUENCE = 0

# Delay between packets
PROCESS_DELAY = 0.1

# Reproducible random payloads
RANDOM_SEED = 20260918

LOG_DIR = Path("Fuzz_logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "case6_results.txt"


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

    crc = crc_accumulate(
        crc_extra,
        crc
    )

    return crc


# ============================================================
# MAVLink MESSAGE MAP
# ============================================================

MESSAGE_MAP = mavlink2.mavlink_map


# ============================================================
# BUILD MAVLink 2 PACKET
# ============================================================

def build_packet(payload, sequence):

    payload_length = len(payload)

    # --------------------------------------------------------
    # MAVLink 2 header
    # --------------------------------------------------------

    header = bytes([
        payload_length,
        0,                          # incompatibility flags
        0,                          # compatibility flags
        sequence & 0xFF,
        SYSTEM_ID & 0xFF,
        COMPONENT_ID & 0xFF,

        # 24-bit message ID
        MSG_ID & 0xFF,
        (MSG_ID >> 8) & 0xFF,
        (MSG_ID >> 16) & 0xFF,
    ])

    # --------------------------------------------------------
    # CRC_EXTRA
    # --------------------------------------------------------

    if MSG_ID in MESSAGE_MAP:
        crc_extra = MESSAGE_MAP[MSG_ID].crc_extra
    else:
        crc_extra = 0

    # --------------------------------------------------------
    # Calculate CRC
    # --------------------------------------------------------

    crc = mavlink_crc(
        header + payload,
        crc_extra
    )

    # Low byte first
    crc_bytes = bytes([
        crc & 0xFF,
        (crc >> 8) & 0xFF
    ])

    # --------------------------------------------------------
    # Complete MAVLink 2 frame
    # --------------------------------------------------------

    packet = (
        bytes([0xFD])
        + header
        + payload
        + crc_bytes
    )

    return packet


# ============================================================
# SITL MONITOR
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

rng = random.Random(
    RANDOM_SEED
)

sequence = START_SEQUENCE
test_id = 0

total_tests = (
    END_PAYLOAD_LENGTH
    - START_PAYLOAD_LENGTH
    + 1
)


print("========================================")
print("MAVLink Test Case 6")
print("========================================")
print(
    f"SITL            : "
    f"{SITL_IP}:{SITL_PORT}"
)
print(
    f"Message ID      : "
    f"{MSG_ID}"
)
print(
    f"Payload lengths : "
    f"{START_PAYLOAD_LENGTH} -> "
    f"{END_PAYLOAD_LENGTH}"
)
print(
    "Payload pattern : RANDOM"
)
print(
    f"Random seed     : "
    f"{RANDOM_SEED}"
)
print(
    f"Total tests     : "
    f"{total_tests}"
)
print(
    "Mode            : "
    "ONE PERSISTENT TCP CONNECTION"
)
print(
    f"Delay           : "
    f"{PROCESS_DELAY} seconds"
)
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
        "MAVLink Test Case 6\n"
    )

    log.write(
        "===================\n"
    )

    log.write(
        f"MSG_ID: {MSG_ID}\n"
    )

    log.write(
        f"SYSTEM_ID: {SYSTEM_ID}\n"
    )

    log.write(
        f"COMPONENT_ID: {COMPONENT_ID}\n"
    )

    log.write(
        "PAYLOAD_PATTERN: RANDOM\n"
    )

    log.write(
        f"RANDOM_SEED: {RANDOM_SEED}\n"
    )

    log.write(
        "MODE: ONE PERSISTENT TCP CONNECTION\n\n"
    )


    # ========================================================
    # TEST LOOP
    # ========================================================

    for payload_length in range(
        START_PAYLOAD_LENGTH,
        END_PAYLOAD_LENGTH + 1
    ):

        test_id += 1


        # ----------------------------------------------------
        # Generate random payload
        # ----------------------------------------------------

        payload = bytes(
            rng.getrandbits(8)
            for _ in range(payload_length)
        )


        # ----------------------------------------------------
        # Build MAVLink 2 frame
        # ----------------------------------------------------

        packet = build_packet(
            payload,
            sequence
        )


        # ----------------------------------------------------
        # Send
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
        # Allow SITL to process
        # ----------------------------------------------------

        time.sleep(
            PROCESS_DELAY
        )


        # ----------------------------------------------------
        # Monitor SITL
        # ----------------------------------------------------

        sitl_status = get_sitl_status()


        # ----------------------------------------------------
        # Save readable log
        # ----------------------------------------------------

        log.write(
            f"TEST_ID: {test_id}\n"
        )

        log.write(
            f"MSG_ID: {MSG_ID}\n"
        )

        log.write(
            f"PAYLOAD_LENGTH: "
            f"{payload_length}\n"
        )

        log.write(
            f"SEQUENCE: {sequence}\n"
        )

        log.write(
            f"PAYLOAD_HEX: "
            f"{payload.hex(' ')}\n"
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
        # Terminal output
        # ----------------------------------------------------

        print(
            f"[TX] Test {test_id:03d} | "
            f"MsgID {MSG_ID:03d} | "
            f"Len {payload_length:03d} | "
            f"TCP {tcp_status} | "
            f"SITL "
            f"{sitl_status['SITL_PROCESS']} | "
            f"Port "
            f"{sitl_status['PORT_5760']} | "
            f"{sitl_status['RESULT']}"
        )


        # ----------------------------------------------------
        # Stop if SITL disappears
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
                f"[!!!] Payload length: "
                f"{payload_length}"
            )

            break


        # ----------------------------------------------------
        # Next sequence number
        # ----------------------------------------------------

        sequence = (
            sequence + 1
        ) & 0xFF


# ============================================================
# CLOSE
# ============================================================

sock.close()


print("\n========================================")
print("CASE 6 COMPLETED")
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