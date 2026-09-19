from pymavlink import mavutil

connection= mavutil.mavlink_connection("tcp:192.168.18.6:5760")

print("Connecting to Arducopter SITL . . . ")
print("Waiting for heartbeat")


msg=connection.wait_heartbeat(timeout=30)

if msg is None:
    print("Error: No heartbeat is received.")

else:
    print("MAVLink connection is successful!")
    print("System ID: ",connection.target_system)
    print("Component ID: ", connection.target_component)
    print("Heartbeat: ",msg)