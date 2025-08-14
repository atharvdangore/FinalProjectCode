from machine import Pin, ADC, PWM
import time
from ir import make_sensors

# Pins / settings
ir_sensors = [26, 27, 28]
touch_button = 15
buzz = 16

buzz_frq   = 2500
buzz_vol   = 12000
chirp_time = 120
TL_time    = 5000
chirp_cool = 80

# Pin Initialization
touch = Pin(touch_button, Pin.IN, Pin.PULL_DOWN)    #TOUCH
touch_active   = False                              #TOUCH
flight_active  = False                              #TOUCH
touch_start_ms = 0                                  #TOUCH

Pin(buzz, Pin.OUT, value=0)     #BUZZER
buzzer_pwm = PWM(Pin(buzz))     #BUZZER
buzzer_pwm.freq(buzz_frq)       #BUZZER
buzzer_pwm.duty_u16(0)          #BUZZER
buzz_end_time = 0               #BUZZER
last_chirp_ms = 0               #BUZZER

#######################################
# Buzzer DEFS
#######################################
def buzz_for(ms, duty=buzz_vol):
    #buzz timer
    global buzz_end_time
    buzzer_pwm.duty_u16(duty)  # enable output
    buzz_end_time = time.ticks_add(time.ticks_ms(), ms)

def buzz_off():
    global buzz_end_time
    if buzz_end_time and time.ticks_ms() >= buzz_end_time:
        buzzer_pwm.duty_u16(0)  # Turn off buzzer
        buzz_end_time = 0

def chirp():
    global last_chirp_ms
    now = time.ticks_ms()
    if now - last_chirp_ms >= chirp_cool:
        buzz_for(chirp_time)
        last_chirp_ms = now

#######################################
# Touch DEFS
#######################################
def drone_switch():
    
    # TAKEOFF - 3s
    # LAND - 1s

    global touch_active, flight_active, touch_start_ms
    pressed = touch.value() == 1

    if pressed and not touch_active:
        touch_active = True
        touch_start_ms = time.ticks_ms()
    elif not pressed and touch_active:
        touch_active = False

    if touch_active:
        held = time.ticks_diff(time.ticks_ms(), touch_start_ms)
        if not flight_active and held >= 3000:
            flight_active = True
            return 1
        if flight_active and held >= 1000:
            flight_active = False
            return 0
    return None

#######################################
# Flight loop
#######################################
def lookout(sensors):
    """While flying: watch sensors, chirp on gesture, exit on LAND."""
    while True:
        buzz_off()

        if drone_switch() == 0:
            print("LAND")
            buzz_for(TL_time)   # 5s tone
            return

        for s in sensors:
            dur = s.step()
            if dur is not None:
                print(f"{s.index}:{dur}")
                chirp()

        time.sleep_ms(10)

#######################################
# Main
#######################################
def main():
    sensors = make_sensors(ir_sensors)
    print("Calibrated. Ready.")

    while True:
        buzz_off()

        if drone_switch() == 1:
            print("TAKEOFF")
            buzz_for(TL_time)   # 5s tone
            time.sleep(3)
            lookout(sensors)

        time.sleep_ms(100)

if __name__ == "__main__":
    main()
