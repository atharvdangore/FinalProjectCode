from machine import ADC, Pin
import time

buffer = 10
alpha = 0.05
baseline_time = 3000
idle_gap = 500
min_gesture_time = 150
min_speed_thresh = 3000
min_idle_thresh = 500

class IRGestureSensor:

    def __init__(self, pin_num, index=0):
        # Initialize analog IR sensors
        self.index = index
        self._adc = ADC(Pin(pin_num))
        self._avg_buf = []
        first = self._adc.read_u16()
        self._prev_filtered = first
        self._prev_time = time.ticks_ms()

        self.thresh_speed = min_speed_thresh
        self.thresh_idle = min_idle_thresh

        self._in_gesture = False
        self._t_start = None
        self._t_last_active = self._prev_time

    def calibrate(self):
        # Measure IDLE NOISE
        t0 = time.ticks_ms()
        raw_min, raw_max = 65535, 0

        while time.ticks_diff(time.ticks_ms(), t0) < baseline_time:
            v = self._adc.read_u16()
            if v < raw_min: raw_min = v
            if v > raw_max: raw_max = v
            time.sleep_ms(20)

        noise = raw_max - raw_min
        self.thresh_speed = max(min_speed_thresh, noise * 5)
        self.thresh_idle  = max(min_idle_thresh, noise * 2)

    def step(self):
        # Retuyrns gesture duration
        raw = self._adc.read_u16()

        # moving average
        self._avg_buf.append(raw)
        if len(self._avg_buf) > buffer:
            self._avg_buf.pop(0)
        avg = sum(self._avg_buf) / len(self._avg_buf)

        # low-pass filter
        filtered = self._prev_filtered + alpha * (avg - self._prev_filtered)

        # speed calculation
        now = time.ticks_ms()
        dt = time.ticks_diff(now, self._prev_time) / 1000.0
        speed = (filtered - self._prev_filtered) / dt if dt > 0 else 0.0

        # start gesture
        if (not self._in_gesture) and abs(speed) > self.thresh_speed:
            self._in_gesture = True
            self._t_start = now
            self._t_last_active = now

        # update last activity
        if self._in_gesture and abs(speed) > self.thresh_idle:
            self._t_last_active = now

        # end gesture
        ended = None
        if self._in_gesture and time.ticks_diff(now, self._t_last_active) > idle_gap:
            duration = time.ticks_diff(now, self._t_start)
            if duration >= min_gesture_time:
                ended = duration
            self._in_gesture = False

        self._prev_filtered = filtered
        self._prev_time = now
        return ended

def make_sensors(pins):
    """Create and calibrate sensors for given analog pins."""
    sensors = [IRGestureSensor(p, i) for i, p in enumerate(pins)]
    for s in sensors:
        s.calibrate()
    return sensors
