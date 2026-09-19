from pymavlink import mavutil

SITL_IP = "192.168.18.6"
SITL_PORT = 5760


def main():
    print(f"[+] Connecting to tcp:{SITL_IP}:{SITL_PORT}")

    connection = mavutil.mavlink_connection(
        f"tcp:{SITL_IP}:{SITL_PORT}"
    )

    connection.wait_heartbeat(timeout=30)

    print("[+] MAVLink connection is successful!")
    print(f"System ID: {connection.target_system}")
    print(f"Component ID: {connection.target_component}")

    msg = connection.recv_match(
        blocking=True,
        timeout=10,
    )

    if msg is not None:
        print(
            f"[RX] {msg.get_type()} "
            f"sys={msg.get_srcSystem()} "
            f"comp={msg.get_srcComponent()}"
        )
        raw = msg.get_msgbuf()
        print(f"[RX RAW] {raw.hex(' ')}")


if __name__ == "__main__":
    main()
