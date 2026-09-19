import time
import random 
from pathlib import Path
from pymavlink import mavutil


#configurations


sitlip='192.168.18.6'
sitlport=5760

logdir=Path("Fuzz_logs")
logdir.mkdir(exist_ok=True)

randomseed=12345
random.seed(randomseed)



#connection


def connectsitl():
    print(f"[+] Connecting to {sitlip}:{sitlport}")
    connection=mavutil.mavlink_connection(f"tcp:{sitlip}:{sitlport}")
    print("[+] Waiting for heartbeat...")
    heartbeat=connection.wait_heartbeat(timeout=30)

    if heartbeat is None:
        raise RuntimeError("No heartbeat received from SITL.")

    print("[+] MAVLink connection established")
    print("[+] System ID ",connection.target_system)
    print("[+] Component ID ",connection.target_component)
    return connection


#receive msg


def recmsg(connection):
    msg=connection.recv_match(blocking=True,timeout=5)
    if msg is None:
        return None
    print(
        f"[RX]  {msg.get_type()}"
        f"sys=  {msg.get_srcSystem()}"
        f"comp= {msg.get_srcComponent()}"
    )
    return msg



#save test


def savetestcase(testid,data):
    filename=logdir / f"test_{testid:06d}.bin"
    with open(filename,'ab') as f:
        f.write(data)
        f.write(b'\n')

    return filename



#main


def main():
    print('='*60)
    print("MAVLink SITL Fuzzer - Baseline")
    print('='*60)
    print(f"[+] Random Seed: {randomseed}")

    connection=connectsitl()
    print()
    print("[+] Receiving one MAVLink message...")
    print()

    msg=recmsg(connection)

    if msg is not None:
        raw=msg.get_msgbuf()
        print()
        print("[+] Message type:")
        print(f"    {msg.get_type()}")
        print("[+] Raw MAVLink packet:")
        print(f"    {raw.hex()}")
        print("[+] Packet length")
        print(f"    {len(raw)} bytes")
        savedfile = savetestcase(1, raw)
        print(f"[+] Saved test case: {savedfile}")

    else:
        print("[-] No MAVLink message received.")

    print()
    print("[+] Baseline test finished")


if __name__ == "__main__":
    main()

