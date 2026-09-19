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

# Keep message ID fixed so the intentional mutation is
# the payload-length field.
MSG_ID = 0

SYSTEM_ID = 255
COMPONENT_ID = 0

START_SEQUENCE = 0

# Reproducible payloads
RANDOM_SEED = 20260918

# Give SITL time to process the malformed frame
PROCESS_DELAY = 0.5

LOG_DIR = Path("Fuzz_logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "case7_results.txt"


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

if MSG_ID not in MESSAGE_MAP:
    raise RuntimeError(
        f"Message ID {MSG_ID} not found in pymavlink."
    )

CRC_EXTRA = MESSAGE_MAP[MSG_ID].crc_extra


# ============================================================
# BUILD MALFORMED MAVLink 2 FRAME
# ============================================================

def build_packet(
    actual_payload,
    declared_length,
    sequence
):

    actual_length = len(actual_payload)

    # --------------------------------------------------------
    # Sanity check
    # --------------------------------------------------------

    if not 0 <= declared_length <= 255:
        raise ValueError(
            f"Declared MAVLink 2 length must be 0..255, "
            f"got {declared_length}"
        )

    if not 1 <= actual_length <= 255:
        raise ValueError(
            f"Actual payload length must be 1..255, "
            f"got {actual_length}"
        )

    if declared_length == actual_length:
        raise ValueError(
            "Case 7 requires declared length != actual length."
        )

    # --------------------------------------------------------
    # MAVLink 2 header
    #
    # IMPORTANT:
    # The header contains the MALFORMED declared length.
    # The actual payload remains the full actual_payload.
    # --------------------------------------------------------

    header = bytes([
        declared_length,
        0,                              # incompatibility flags
        0,                              # compatibility flags
        sequence & 0xFF,
        SYSTEM_ID & 0xFF,
        COMPONENT_ID & 0xFF,

        # 24-bit message ID
        MSG_ID & 0xFF,
        (MSG_ID >> 8) & 0xFF,
        (MSG_ID >> 16) & 0xFF,
    ])

    # --------------------------------------------------------
    # Calculate CRC from the bytes actually placed on wire.
    #
    # The malformed length is therefore part of the CRC input.
    # --------------------------------------------------------

    crc = mavlink_crc(
        header + actual_payload,
        CRC_EXTRA
    )

    crc_bytes = bytes([
        crc & 0xFF,
        (crc >> 8) & 0xFF
    ])

    # --------------------------------------------------------
    # Complete malformed frame
    # --------------------------------------------------------

    packet = (
        bytes([0xFD])
        + header
        + actual_payload
        + crc_bytes
    )

    return packet


# ============================================================
# SEND ONE TEST
# ============================================================

def send_one_test(packet):

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    try:

        sock.settimeout(5)

        print("[DEBUG] Connecting to SITL...")

        sock.connect(
            (SITL_IP, SITL_PORT)
        )

        print("[DEBUG] TCP CONNECT SUCCESS")

        print(
            f"[DEBUG] Sending {len(packet)} bytes..."
        )

        sock.sendall(packet)

        print("[DEBUG] SEND SUCCESS")

        # Let SITL process the malformed frame.
        time.sleep(PROCESS_DELAY)

        # Explicitly signal end of this test's data.
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

    except Exception as e:

        try:
            sock.close()
        except OSError:
            pass

        return (
            f"FAILED: "
            f"{type(e).__name__}: {e}"
        )


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
        except OSError:
            pass

        return {
            "SITL_PROCESS": "UNKNOWN",
            "PORT_5760": "UNKNOWN",
            "RESULT": f"MONITOR_ERROR: {e}"
        }


# ============================================================
# TEST CONFIGURATION
# ============================================================

tests = []

# ------------------------------------------------------------
# 7A: declared length = actual length - 1
# Actual lengths: 1..255
# ------------------------------------------------------------

for actual_length in range(1, 256):

    tests.append({
        "subcase": "7A_MINUS_ONE",
        "actual_length": actual_length,
        "declared_length": actual_length - 1,
    })


# ------------------------------------------------------------
# 7B: declared length = actual length + 1
# Actual lengths: 1..254
#
# 255 + 1 would be 256, which cannot be represented in the
# one-byte MAVLink 2 payload-length field.
# ------------------------------------------------------------

for actual_length in range(1, 255):

    tests.append({
        "subcase": "7B_PLUS_ONE",
        "actual_length": actual_length,
        "declared_length": actual_length + 1,
    })


TOTAL_TESTS = len(tests)


# ============================================================
# MAIN
# ============================================================

rng = random.Random(
    RANDOM_SEED
)

sequence = START_SEQUENCE

print("========================================")
print("MAVLink Test Case 7")
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
    "Subcase 7A      : "
    "declared = actual - 1"
)
print(
    "Subcase 7B      : "
    "declared = actual + 1"
)
print(
    f"Total tests     : "
    f"{TOTAL_TESTS}"
)
print(
    f"Random seed     : "
    f"{RANDOM_SEED}"
)
print(
    "Mode            : "
    "ONE TCP CONNECTION PER TEST"
)
print(
    f"Delay           : "
    f"{PROCESS_DELAY} seconds"
)
print("========================================")


with open(
    LOG_FILE,
    "w"
) as log:

    log.write(
        "MAVLink Test Case 7\n"
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
        f"RANDOM_SEED: {RANDOM_SEED}\n"
    )

    log.write(
        "SUBCASE_7A: declared = actual - 1\n"
    )

    log.write(
        "SUBCASE_7B: declared = actual + 1\n"
    )

    log.write(
        "MODE: ONE TCP CONNECTION PER TEST\n\n"
    )


    # ========================================================
    # RUN TESTS
    # ========================================================

    for test_id, test in enumerate(
        tests,
        start=1
    ):

        actual_length = test["actual_length"]
        declared_length = test["declared_length"]
        subcase = test["subcase"]


        # ----------------------------------------------------
        # Generate deterministic random payload
        # ----------------------------------------------------

        payload = bytes(
            rng.getrandbits(8)
            for _ in range(actual_length)
        )


        # ----------------------------------------------------
        # Build malformed frame
        # ----------------------------------------------------

        packet = build_packet(
            payload,
            declared_length,
            sequence
        )


        # ----------------------------------------------------
        # Send
        # ----------------------------------------------------

        tcp_status = send_one_test(
            packet
        )


        # ----------------------------------------------------
        # Monitor SITL
        # ----------------------------------------------------

        sitl_status = get_sitl_status()


        # ----------------------------------------------------
        # Save readable result
        # ----------------------------------------------------

        log.write(
            f"TEST_ID: {test_id}\n"
        )

        log.write(
            f"SUBCASE: {subcase}\n"
        )

        log.write(
            f"MSG_ID: {MSG_ID}\n"
        )

        log.write(
            f"DECLARED_LENGTH: "
            f"{declared_length}\n"
        )

        log.write(
            f"ACTUAL_LENGTH: "
            f"{actual_length}\n"
        )

        log.write(
            f"LENGTH_DELTA: "
            f"{declared_length - actual_length}\n"
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
            f"{subcase} | "
            f"Declared {declared_length:03d} | "
            f"Actual {actual_length:03d} | "
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
                f"[!!!] Test ID: {test_id}"
            )

            print(
                f"[!!!] Subcase: {subcase}"
            )

            print(
                f"[!!!] Declared: "
                f"{declared_length}"
            )

            print(
                f"[!!!] Actual: "
                f"{actual_length}"
            )

            break


        # ----------------------------------------------------
        # Advance sequence
        # ----------------------------------------------------

        sequence = (
            sequence + 1
        ) & 0xFF


        # Small pause before the next TCP connection
        time.sleep(0.2)


print("\n========================================")
print("CASE 7 COMPLETED")
print(
    f"Tests executed: {test_id}"
)
print(
    f"Expected tests: {TOTAL_TESTS}"
)
print(
    f"Log: {LOG_FILE}"
)
print("========================================")