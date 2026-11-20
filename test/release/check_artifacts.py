#!/usr/bin/env python3
"""Verify that every delivered firmware image matches its build and manifest."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
from zipfile import ZipFile


def require(valid, error):
    if not valid:
        raise ValueError(error)


def intel_hex(file):
    addresses = {}
    base = 0
    eof = False
    for line in file.read_text().splitlines():
        require(line.startswith(":"), "Invalid Intel HEX record")
        payload = bytes.fromhex(line[1:])
        size, address, kind = struct.unpack(">BHB", payload[:4])
        require(size + 5 == len(payload) and not sum(payload) % 256, "Invalid Intel HEX checksum")
        data = payload[4:-1]
        if kind == 0:
            addresses.update((base + address + i, byte) for i, byte in enumerate(data))
        elif kind in (2, 4):
            base = int.from_bytes(data, "big") << (4 if kind == 2 else 16)
        elif kind == 1:
            eof = True
            break
    require(addresses and eof, "Intel HEX has no complete application")
    return addresses


def check_nrf(zip_path, uf2_path, hex_path):
    with ZipFile(zip_path) as archive:
        require(archive.testzip() is None, "Corrupt DFU ZIP")
        manifest = json.loads(archive.read("manifest.json"))["manifest"]
        application = manifest["application"]
        require(not any(key in manifest for key in ("softdevice", "bootloader", "softdevice_bootloader")),
                "A release DFU package must only contain the application")
        binary = archive.read(application["bin_file"])
        require(archive.read(application["dat_file"]), "Missing DFU init packet")

    raw = uf2_path.read_bytes()
    count = len(raw) // 512
    require(count and len(raw) % 512 == 0, "Incomplete UF2")
    addresses = {}
    for index, offset in enumerate(range(0, len(raw), 512)):
        m0, m1, flags, addr, size, block, total, family = struct.unpack_from("<8I", raw, offset)
        end, = struct.unpack_from("<I", raw, offset + 508)
        require((m0, m1, end) == (0x0A324655, 0x9E5D5157, 0x0AB16F30) and
                flags & 0x2000 and family == 0xADA52840 and
                index == block and total == count and 0 < size <= 476,
                f"Invalid nRF52840 UF2 block {index}")
        for i in range(size):
            require(addr + i not in addresses, "Overlapping UF2 records")
            addresses[addr + i] = raw[offset + 32 + i]

    source = intel_hex(hex_path)
    base = min(source)
    require(min(addresses) == base and len(binary) == max(source) - base + 1,
            "Image address or application length mismatch")
    for addr, byte in source.items():
        require(addresses.get(addr) == byte and binary[addr - base] == byte,
                f"DFU ZIP or UF2 differs from the application at 0x{addr:x}")


def verify(environment, build, output, commit):
    stem = f"{environment}-{commit[:12]}"
    manifest_path = output / (stem + ".json")
    manifest = json.loads(manifest_path.read_text())
    require(manifest["environment"] == environment and manifest["commit"] == commit, "Wrong manifest identity")
    entries = dict((name, digest) for digest, name in
                   (line.split(maxsplit=1) for line in (output / (stem + ".sha256")).read_text().splitlines()))
    require(set(entries) == {*manifest["files"], manifest_path.name}, "SHA256 list disagrees with manifest")
    for name, digest in entries.items():
        require(Path(name).name == name and re.fullmatch("[a-f0-9]{64}", digest), "Invalid SHA256 entry")
        require(hashlib.sha256((output / name).read_bytes()).hexdigest() == digest, f"Bad SHA256 for {name}")
    if set(manifest["files"]) == {stem + ".dfu.zip", stem + ".uf2"}:
        check_nrf(output / (stem + ".dfu.zip"), output / (stem + ".uf2"), build / "firmware.hex")
    elif set(manifest["files"]) == {stem + ".application.bin", stem + ".full-flash.bin"}:
        for suffix, file in (("application", "firmware.bin"), ("full-flash", "firmware-merged.bin")):
            image = (output / (stem + f".{suffix}.bin")).read_bytes()
            require(image and image == (build / file).read_bytes(), f"Wrong {suffix} ESP image")
    else:
        raise ValueError("Unknown firmware artifact contract")
    print(f"PASS {environment} artifact manifest, SHA256 and image contents")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("environment")
    parser.add_argument("build", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("commit")
    args = parser.parse_args()
    verify(args.environment, args.build, args.output, args.commit)
