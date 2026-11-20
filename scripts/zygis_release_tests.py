#!/usr/bin/env python3
"""Run repeatable Žygis release checks on build hosts and USB benches."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

from zygis import ROOT, query_frame, wio_port
from zygis_release import targets

COMMON = (
    "test_cycle.py", "test_dispatch.py", "test_persistence.py",
    "test_serial_cli.py", "test_tracking_menu.py", "test_game_priority.py",
)
KIT = "LilyGo_T-Echo-Lite_keyshield_zygis"
ARENA = "WioTrackerL1_zygis_arena"


def run(path, *args):
    subprocess.run([sys.executable, str(ROOT / path), *map(str, args)], cwd=ROOT, check=True)


def host(environment, output):
    for test in COMMON:
        run("test/tracking/" + test)
    if environment == KIT:
        run("test/tracking/test_kit_ux.py")
    if environment == ARENA:
        run("test/multiplayer/test_multiplayer.py")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    run("test/release/check_artifacts.py", environment, ROOT / ".pio/build" / environment, output, commit)
    (output / f"{environment}-{commit[:12]}.tests.json").write_text(json.dumps({
        "environment": environment,
        "commit": commit,
        "host": "passed",
        "artifact": "passed",
        "usb": "not run",
    }, indent=2) + "\n")


def bench(environment, serial_number, peer, version, output):
    import serial
    from serial.tools.list_ports import comports

    if environment == KIT:
        port = next((p for p in comports() if p.serial_number == serial_number
                     and (p.vid, p.pid) == (0x239A, 0x8029)), None)
        if port is None:
            raise ValueError("Connect the T-Echo Lite Kit")
    else:
        port = wio_port(serial_number)
    with serial.Serial(port.device, 115200, timeout=0.2, write_timeout=2) as conn:
        reply = query_frame(conn, b"\x16\x0e", 13)
        installed = reply[60:80].split(b"\0")[0].decode()
        if installed != version:
            raise ValueError(f"{environment} expected {version}, device reports {installed}")
        cli = query_frame(conn, b"\x42ver", 29)[1:].decode()
        if "+test" not in cli:
            raise ValueError("USB menu tests require a firmware build with SOLO_TEST_HOOKS")
    if environment == KIT:
        run("scripts/zygis_kit_menus.py", serial_number, "--peer-serial", peer, "--output", output)
    else:
        run("tools/hwtest.py", "--port", port.device, "--only", "identity,keys,screens,screenshot")
        run("scripts/zygis.py", "test-wio-pair", serial_number, peer, "--smoke")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("environment", choices=targets())
    parser.add_argument("--output", type=Path, default=ROOT / "out/release")
    parser.add_argument("--usb", nargs=3, metavar=("DEVICE_SERIAL", "PEER_SERIAL", "VERSION"),
                        help="check an attached bench build instead of release artifacts")
    args = parser.parse_args()
    if args.usb:
        bench(args.environment, *args.usb, args.output)
    else:
        host(args.environment, args.output)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        sys.exit(str(exc))
