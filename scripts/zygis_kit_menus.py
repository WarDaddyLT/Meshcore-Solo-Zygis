#!/usr/bin/env python3
"""Drive the T-Echo Lite Kit's real menu handlers on a Solo bench build over USB."""

import argparse
from pathlib import Path
import struct
import sys
import time
import zlib

from zygis import query_frame, read_frame


def check(condition, detail):
    if not condition:
        raise RuntimeError(detail)


def png_chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))


class Kit:
    def __init__(self, connection, output):
        self.connection = connection
        self.output = output

    def cli(self, command):
        return query_frame(self.connection, bytes((66,)) + command.encode(), 29)[1:].decode()

    def where(self):
        return self.cli("ui").removeprefix("> ").split("|", 1)[0]

    def key(self, name, count=1):
        for _ in range(count):
            check(self.cli("key " + name) == "OK", f"Key {name} rejected")
            time.sleep(0.28)

    def expect(self, expected):
        until = time.monotonic() + 3
        while True:
            got = self.where()
            if got == expected:
                return
            if time.monotonic() >= until:
                raise RuntimeError(f"Expected {expected}, got {got}")
            time.sleep(0.12)

    def screenshot(self, name):
        self.connection.write(b"<\x01\x00\x7e")
        parts = {}
        deadline = time.monotonic() + 8
        while (frame := read_frame(self.connection, deadline)) is not None:
            if frame[0] != 0x7E or len(frame) < 11:
                continue
            _, kind, rotation, width, height, index, count = struct.unpack("<BBBHHHH", frame[:11])
            parts[index] = frame[11:]
            if len(parts) == count:
                break
        else:
            raise RuntimeError("Incomplete USB framebuffer")

        width_native, height_native = (height, width) if rotation & 1 else (width, height)
        stride = (width_native + 7) // 8
        bits = b"".join(parts[i] for i in range(count))
        check(kind == 1 and len(bits) == stride * height_native and rotation < 4, "Not a kit e-paper framebuffer")
        raster = bytearray()
        for y in range(height):
            raster.append(0)
            for x in range(width):
                px, py = ((x, y), (width_native - 1 - y, x), (width_native - 1 - x, height_native - 1 - y),
                          (y, height_native - 1 - x))[rotation]
                raster.append(255 if bits[py * stride + px // 8] & (0x80 >> (px % 8)) else 0)
        png = b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
        png += png_chunk(b"IDAT", zlib.compress(raster)) + png_chunk(b"IEND", b"")
        (self.output / (name + ".png")).write_bytes(png)
        return tuple(raster[y * (width + 1) + 1 + width // 2:(y + 1) * (width + 1)] for y in range(26))

    def open_card(self, label, expected):
        if self.where() != "home/carousel":
            self.key("home")
            self.expect("home/carousel")
        for _ in range(16):
            if self.cli("kit selection") == label:
                break
            self.key("down")
        else:
            raise RuntimeError(f"Card not visible: {label}")
        self.key("enter")
        self.expect(expected)


def walk(kit):
    failures = []

    def verify(label, action):
        try:
            action()
        except (RuntimeError, OSError) as exc:
            failures.append(f"FAIL {label}: {exc}")
            print(failures[-1], flush=True)
        else:
            print(f"PASS {label}", flush=True)

    def splash():
        kit.expect("splash")
        kit.screenshot("splash")
        kit.key("enter")
        kit.expect("home/carousel")

    verify("Splash waits for input", splash)
    for label, screen, inner in (
        ("Messages", "messages/menu", None), ("Clock", "clock/menu", None),
        ("Favourites", "home/Favourites", None), ("Status", "home/Status", "status"),
        ("Bluetooth", "home/Bluetooth", None), ("Advert", "home/Advert", "home/advert-review"),
        ("Settings", "home/Settings", "settings"), ("Map", "home/Map", "trail"),
        ("Tools", "home/Tools", "tools"), ("Power", "home/Power", None),
    ):
        def card():
            kit.open_card(label, screen)
            if inner:
                kit.key("enter")
                kit.expect(inner)
            kit.screenshot("card-" + label.lower())
            if label == "Advert":
                kit.key("cancel")
                kit.expect("home/Advert")
        verify(label, card)

    for index, name in enumerate(("alarm", "timer", "stopwatch", "calendar")):
        def clock_view():
            kit.open_card("Clock", "clock/menu")
            kit.key("down", index)
            kit.key("enter")
            kit.expect("clock/" + name)
            kit.screenshot("clock-" + name)
            kit.key("cancel")
            kit.expect("clock/menu")
        verify("Clock > " + name, clock_view)

    for index, name in enumerate(("direct", "channels", "rooms", "quick")):
        def message_view():
            kit.open_card("Messages", "messages/menu")
            kit.key("down", index)
            kit.key("enter")
            kit.expect("home/quick" if name == "quick" else "messages/" + name)
            kit.screenshot("messages-" + name)
        verify("Messages > " + name, message_view)

    def settings_tracking():
        kit.open_card("Settings", "home/Settings")
        kit.key("enter", 2)
        kit.expect("settings")
        kit.screenshot("settings-tracking")
        check(kit.cli("verify").startswith(("READY:", "BLOCKED:")), "Tracking CLI unavailable")
    verify("Settings > Tracking and local CLI", settings_tracking)

    for section, entries in enumerate((
        (("Nodes", "nearby"), ("Live Share", "live-share"), ("Trail", "trail"),
         ("Locator", "locator"), ("Compass", "compass")),
        (("SOS", "sos"), ("Remote Bot", "bot"), ("Auto-Advert", "auto-advert"),
         ("Repeater", "repeater"), ("Admin", "nearby")),
        (("Clock Tools", "clock/menu"), ("Ringtone Editor", "ringtone")),
    )):
        for index, (label, screen) in enumerate(entries):
            def tool():
                kit.open_card("Tools", "home/Tools")
                kit.key("enter")
                kit.expect("tools")
                kit.key("down", section)
                kit.key("enter")
                kit.key("down", index + 1)
                kit.key("enter")
                kit.expect(screen)
                kit.screenshot("tool-" + label.lower().replace(" ", "-"))
            verify("Tools > " + label, tool)

    def lock():
        kit.key("home")
        kit.expect("home/carousel")
        check(kit.cli("kit lock") == "OK", "Lock transition rejected")
        try:
            kit.expect("kit/lock")
            kit.key("down")
            kit.expect("kit/lock")
            kit.screenshot("clock-lock")
        finally:
            if kit.where() == "kit/lock":
                kit.cli("kit lock")
        kit.expect("home/carousel")
    verify("Clock lock blocks normal navigation and unlock returns to carousel", lock)
    print(f"Menu smoke check finished with {len(failures)} failure(s)", flush=True)
    return bool(failures)


def main():
    import serial
    from serial.tools.list_ports import comports

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kit_serial")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--peer-serial", help="run the radio checks and verify an unread badge while locked")
    parser.add_argument("--radio-only", action="store_true", help="skip the menu walk")
    args = parser.parse_args()
    port = next((p for p in comports() if p.serial_number == args.kit_serial
                 and (p.vid, p.pid) == (0x239A, 0x8029)), None)
    check(port is not None, "Kit USB port unavailable")
    args.output.mkdir(parents=True, exist_ok=True)
    with serial.Serial(port.device, 115200, timeout=0.2, write_timeout=2) as connection:
        kit = Kit(connection, args.output)
        check("+test" in kit.cli("ver"), "Load a Solo bench build before sending test keys")
        failed = False if args.radio_only else walk(kit)

    if args.peer_serial:
        from zygis_kit_pair import smoke

        before = None
        def unread_badge(radio, received):
            nonlocal before
            kit = Kit(radio.connection, args.output)
            if not received:
                kit.key("home")
                kit.expect("home/carousel")
                check(kit.cli("kit lock") == "OK", "Lock transition rejected")
                kit.expect("kit/lock")
                before = kit.screenshot("lock-before-message")
            else:
                kit.expect("kit/lock")
                deadline = time.monotonic() + 15
                while kit.screenshot("lock-after-message") == before:
                    check(time.monotonic() < deadline,
                          "Unread badge area did not change after a real LoRa message")
                    time.sleep(0.35)
                print("PASS locked unread badge updates after a LoRa message", flush=True)

        try:
            smoke(args.kit_serial, args.peer_serial, on_kit_message=unread_badge)
        finally:
            with serial.Serial(port.device, 115200, timeout=0.2, write_timeout=2) as connection:
                kit = Kit(connection, args.output)
                if kit.where() == "kit/lock":
                    kit.cli("kit lock")
    return failed


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError) as exc:
        sys.exit(str(exc))
