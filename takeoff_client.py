import asyncio
from mavsdk import System
from mavsdk.offboard import OffboardError, VelocityNedYaw
import pickle
import serial
import time
import platform
import numpy as np

# ========= PC–Pico serial =========
os_type = platform.system()
if os_type == "Windows":
    port = "COM3"
elif os_type == "Darwin":
    port = "/dev/tty.usbmodem11101"
else:
    raise Exception("Unsupported OS")

# Non-blocking-ish: set a tiny timeout and poll .in_waiting
s = serial.Serial(port, 115200, timeout=0)

# ========= ML model =========
filename = 'SVM.sav'
load_model = pickle.load(open(filename, 'rb'))
print("PC client ready, waiting for data...")

# ========= Streaming rate / helpers =========
rate_hz = 25
dt = 1.0 / rate_hz

def parse_pico_line():
    """Return a decoded line if available, else None. Expected 'id:duration' or 'TAKEOFF'/'LAND'."""
    if s.in_waiting > 0:
        raw = s.readline()
        if not raw:
            return None
        try:
            return raw.decode(errors="ignore").strip()
        except Exception:
            return None
    return None

def dir_to_velocity(direction, speed):
    # LOCAL_NED: +X forward, +Y right, -Y left, -X backward, +Z down
    if direction == "3":     # backward
        return VelocityNedYaw(-speed, 0.0, 0.0, 0.0)
    elif direction == "2":   # left
        return VelocityNedYaw(0.0, -speed, 0.0, 0.0)
    elif direction == "1":   # forward
        return VelocityNedYaw(speed, 0.0, 0.0, 0.0)
    elif direction == "0":   # right
        return VelocityNedYaw(0.0, speed, 0.0, 0.0)
    else:
        return VelocityNedYaw(0.0, 0.0, 0.0, 0.0)

async def drone_takeoff(drone):
    await drone.action.takeoff()
    print("Takeoff command sent!")
    await asyncio.sleep(5)

    # Prime Offboard with zero-velocity setpoints (not position) for ~0.5 s
    for _ in range(int(0.5 / dt)):
        await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
        await asyncio.sleep(dt)

    try:
        await drone.offboard.start()
        print("Offboard mode started!")
    except OffboardError as e:
        print(f"Failed to start offboard mode: {e._result.result}")
        return False

    # Small climb using velocity (negative Z is up)
    print("Climbing...")
    for _ in range(int(3.0 / dt)):
        await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, -1.0, 0.0))
        await asyncio.sleep(dt)

    print("Hovering in place...")
    return True

async def drone_land(drone):
    print("Landing...")
    try:
        await drone.offboard.stop()
    except OffboardError:
        pass
    await drone.action.land()
    async for in_air in drone.telemetry.in_air():
        if not in_air:
            print("Landed.")
            break
    return False

async def run():
    drone = System()
    await drone.connect(system_address="udpout://172.18.208.146:14540")
    print("Connecting to drone...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Connected to drone!")
            break

    await drone.action.arm()
    print("Armed!")

    offboard_ready = False

    # Sent at rate_hz
    current_vel = VelocityNedYaw(0.0, 0.0, 0.0, 0.0)
    ticks_remaining = 0  # how long to keep current_vel for a maneuver

    while True:
        line = parse_pico_line()
        if line:
            print(line)
            if line == "TAKEOFF" and not offboard_ready:
                offboard_ready = await drone_takeoff(drone)
            elif line == "LAND" and offboard_ready:
                offboard_ready = await drone_land(drone)
            elif offboard_ready:
                # Check for OFFBOARD mode
                try:
                    sensor_id, dur = line.split(":")
                    duration = float(dur)  # seconds; if Pico sends ms, divide by 1000.0
                except ValueError:
                    print(f"Bad command from Pico: {line!r} (expected 'id:duration')")
                else:
                    # ML gesture → (speed, flight time)
                    gesture = load_model.predict(np.array([[duration]]))[0]
                    print(f"Gesture detected: {gesture}")

                    if gesture == "fast_swat":
                        speed, flightime = 20, 2.5
                    elif gesture == "slow_swat":
                        speed, flightime = 3, 2.5
                    elif gesture == "static":
                        speed, flightime = 10, 0.1

                    current_vel = dir_to_velocity(sensor_id, speed)
                    ticks_remaining = max(1, int(flightime / dt))
                    print(f"Command: {current_vel} for {flightime:.2f}s")

        # Hover Loop at rate_hz
        if offboard_ready:
            # Hold with zero velocity when no maneuver
            if ticks_remaining <= 0:
                current_vel = VelocityNedYaw(0.0, 0.0, 0.0, 0.0)
            else:
                ticks_remaining -= 1

            await drone.offboard.set_velocity_ned(current_vel)
        else:
            pass

        await asyncio.sleep(dt)

asyncio.run(run())
