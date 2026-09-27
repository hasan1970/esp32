"""Turn the Nano's inputs into slide, volume or music controls on the Mac.

    .venv/bin/python controller.py            # slides: B1 = next, B2 = previous
    .venv/bin/python controller.py volume     # volume: B1 = up,   B2 = down
    .venv/bin/python controller.py music      # media keys, see MUSIC below

Slides sends the Right / Left arrow keys to whatever app is in front (Keynote,
PowerPoint, Google Slides, PDF viewers). Music sends the Mac's media keys, so it
works with YouTube Music in Chrome, Spotify, Apple Music, even in the background.
Both need your terminal app allowed once under
System Settings > Privacy & Security > Accessibility.

Only one program can use the port: close status.html / arcade.html tabs first.
"""

import json
import subprocess
import sys
import time

import serial

PORT = "/dev/cu.usbserial-10"
VOLUME_STEP = 6  # percent per press (volume mode)

# macOS media key codes (NX_KEYTYPE_* in IOKit's ev_keymap.h)
SOUND_UP, SOUND_DOWN, MUTE, PLAY, NEXT, PREVIOUS = 0, 1, 7, 16, 17, 18


def osascript(script):
    return lambda: subprocess.run(["osascript", "-e", script], check=False)


def media_key(code):
    from AppKit import NSEvent
    import Quartz

    def press():
        for flags in (0xA00, 0xB00):  # key down, key up
            ev = NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(
                14, (0, 0), flags, 0, 0, None, 8, (code << 16) | flags, -1)
            Quartz.CGEventPost(0, ev.CGEvent())
    return press


# Per mode: press-count key -> (label, action). "enc+"/"enc-" fire once per encoder click.
MODES = {
    "slides": {
        "b1n": ("Next slide", osascript('tell application "System Events" to key code 124')),  # Right arrow
        "b2n": ("Previous slide", osascript('tell application "System Events" to key code 123')),  # Left arrow
    },
    "volume": {
        "b1n": ("Volume up", osascript(f"set volume output volume ((output volume of (get volume settings)) + {VOLUME_STEP})")),
        "b2n": ("Volume down", osascript(f"set volume output volume ((output volume of (get volume settings)) - {VOLUME_STEP})")),
    },
    "music": {
        "b1n": ("Next track", media_key(NEXT)),
        "b2n": ("Previous track", media_key(PREVIOUS)),
        "swn": ("Play / pause", media_key(PLAY)),
        "ebn": ("Mute", media_key(MUTE)),
        "enc+": ("Volume up", media_key(SOUND_UP)),
        "enc-": ("Volume down", media_key(SOUND_DOWN)),
    },
}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "slides"
    if mode not in MODES:
        sys.exit(f"Unknown mode {mode!r}. Use: {' / '.join(MODES)}")
    actions = MODES[mode]

    # Without Accessibility permission macOS silently drops the key events.
    if mode in ("slides", "music"):
        import Quartz
        if not Quartz.CGPreflightPostEventAccess():
            Quartz.CGRequestPostEventAccess()  # opens the macOS permission prompt
            sys.exit("macOS is blocking key events. Allow your terminal app under System Settings > "
                     "Privacy & Security > Accessibility, then run this again.")

    print(f"Mode: {mode}. " + ", ".join(label for label, _ in actions.values()) + ". Ctrl+C to quit.", flush=True)
    while True:
        try:
            port = serial.Serial(PORT, 115200, timeout=1)
        except serial.SerialException:
            time.sleep(1)  # Nano unplugged or port busy: keep waiting
            continue
        print("Nano connected.", flush=True)
        try:
            run(port, actions)
        except serial.SerialException:
            print("Nano disconnected - waiting for it to come back...", flush=True)
            port.close()


def run(port, actions):
    seen = None  # counters from the previous line
    while True:
        line = port.readline().decode(errors="replace").strip()
        try:
            d = json.loads(line)
        except ValueError:
            continue  # partial line while the Nano restarts
        counts = {k: d.get(k, 0) for k in ("b1n", "b2n", "swn", "ebn")}
        if seen is None or any(counts[k] < seen[k] for k in counts):
            seen, enc = counts, d.get("enc", 0)  # first line, or the Nano restarted: new baseline
            continue

        steps = {k: counts[k] - seen[k] for k in counts}
        turn = d.get("enc", 0) - enc
        steps["enc+"], steps["enc-"] = max(turn, 0), max(-turn, 0)
        for key, (label, action) in actions.items():
            for _ in range(steps[key]):
                print(label, flush=True)
                action()
        seen, enc = counts, d.get("enc", 0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
