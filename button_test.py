# Button test for Freenove ESP32-WROVER (MicroPython).
# Run from the Mac:  .venv/bin/mpremote connect /dev/cu.usbserial-10 run button_test.py
#
# Tests two buttons at once:
#   BOOT - the small on-board "BOOT/IO0" button (GPIO0). Works with no wiring.
#   EXT  - the breadboard button: one leg -> GPIO27, other leg -> GND.
# Both use the internal pull-up, so the pin reads 1 when released and 0 when pressed.

import time
from machine import Pin

BUTTONS = {"BOOT": 0, "EXT (GPIO27)": 27}
TEST_SECONDS = 30
DEBOUNCE_MS = 30

state = {}
for name, gpio in BUTTONS.items():
    pin = Pin(gpio, Pin.IN, Pin.PULL_UP)
    level = pin.value()
    state[name] = {"pin": pin, "level": level, "changed": time.ticks_ms(), "presses": 0}
    note = "released (OK)" if level else "reads PRESSED already -> held down, or wiring is shorted to GND"
    print("{:13s} GPIO{:<2d} start: {}".format(name, gpio, note))

print("\nPress each button a few times. Test runs for {} s...\n".format(TEST_SECONDS))
start = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), start) < TEST_SECONDS * 1000:
    now = time.ticks_ms()
    for name, s in state.items():
        level = s["pin"].value()
        if level != s["level"] and time.ticks_diff(now, s["changed"]) > DEBOUNCE_MS:
            s["level"], s["changed"] = level, now
            if level == 0:
                s["presses"] += 1
                print("{:13s} PRESSED   (#{})".format(name, s["presses"]))
            else:
                print("{:13s} released".format(name))
    time.sleep_ms(2)

print("\n=== RESULT ===")
for name, s in state.items():
    ok = s["presses"] > 0 and s["level"] == 1
    print("{:13s} {}  ({} presses)".format(name, "PASS" if ok else "FAIL", s["presses"]))
