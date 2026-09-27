# Streams button + joystick status over USB serial as one JSON line every 50 ms.
# Copied to the board as main.py so it starts on every power-up; status.html reads it.
#
# Wiring (Freenove ESP32-WROVER):
#   BOOT button    GPIO0   on-board, nothing to wire
#   Ext button     GPIO27  other leg -> GND
#   Joystick VRX   GPIO32
#   Joystick VRY   GPIO33
#   Joystick SW    GPIO14
#   Joystick +5V   3.3V    (use 3.3V, not 5V: the ESP32 ADC tops out at ~3.3V)
#   Joystick GND   GND

import time
from machine import ADC, Pin

boot = Pin(0, Pin.IN, Pin.PULL_UP)
ext = Pin(27, Pin.IN, Pin.PULL_UP)
sw = Pin(14, Pin.IN, Pin.PULL_UP)

jx = ADC(Pin(32))
jy = ADC(Pin(33))
for adc in (jx, jy):
    adc.atten(ADC.ATTN_11DB)  # full 0-3.3V range

while True:
    # Buttons are active-low: 1 in the JSON means pressed.
    print('{"boot":%d,"ext":%d,"sw":%d,"x":%d,"y":%d}' % (
        1 - boot.value(), 1 - ext.value(), 1 - sw.value(),
        jx.read_u16() >> 4, jy.read_u16() >> 4))  # 0-4095
    time.sleep_ms(50)
