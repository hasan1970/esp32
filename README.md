# ESP32 / Nano input controller

Buttons, joystick and rotary encoder on an ESP32 (MicroPython) or Arduino Nano, streamed as JSON over USB serial.

- `main.py` — MicroPython script for the ESP32; streams button + joystick state every 50 ms.
- `nano_status/nano_status.ino` — Arduino Nano sketch doing the same.
- `button_test.py` — quick wiring check for the buttons.
- `status.html`, `status_esp32.html` — live status pages (Web Serial, Chrome).
- `arcade.html` — arcade game playable with the controller (keyboard fallback).
- `controller.py` — drives the Mac: `slides` (default), `volume`, or `music` (media keys: next/prev track, play/pause, mute, encoder volume).

```sh
python3 -m venv .venv && .venv/bin/pip install pyserial esptool mpremote
.venv/bin/python controller.py music
```

Only one program can hold the serial port at a time — close the HTML tabs before running `controller.py`.
