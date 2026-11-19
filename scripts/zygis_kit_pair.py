"""Exercise the T-Echo Lite Kit against an existing Wio without replacing its binding."""

from contextlib import ExitStack
import secrets

from zygis import query_frame, wio_port
from zygis_wio_pair import Radio, exchange, require, status_report, wait_message


def empty_slot(radio):
    for slot in reversed(range(radio.max_channels)):
        channel = radio.get_channel(slot)
        if channel[2] == 0 and not any(channel[34:]):
            return slot
    raise RuntimeError("No empty slot for a temporary kit test channel")


def smoke(kit_serial, peer_serial, *, on_kit_message=None):
    import serial
    from serial.tools.list_ports import comports

    kit_port = next((port for port in comports()
                     if port.serial_number == kit_serial and (port.vid, port.pid) == (0x239A, 0x8029)), None)
    if not kit_port:
        raise RuntimeError("T-Echo Lite USB application port is unavailable")

    with ExitStack() as cleanup:
        def connect(port):
            connection = cleanup.enter_context(serial.Serial(port.device, 115200, timeout=0.2, write_timeout=2))
            return Radio(connection, query_frame)

        kit = connect(kit_port)
        peer = connect(wio_port(peer_serial))
        require(kit.version.startswith("K"), "The kit is not running a Žygis Kit build")
        require(kit.slot == 255 or kit.cli("verify").startswith("READY:"),
                "The kit has a stale tracking binding. Repair it before testing.")
        kit_binding = kit.slot
        original_preset = kit.preset
        repeat = kit.query(bytes((22, 14)), 13)[80:81]
        if original_preset != peer.preset:
            def restore_radio():
                kit.query(b"\x0b" + original_preset + repeat, 0)
                frame = kit.query(bytes([1]) + bytes(7) + b"Zygis kit test", 5)
                require(frame[48:58] == original_preset, "Kit LoRa settings did not restore")

            cleanup.callback(restore_radio)
            kit.query(b"\x0b" + peer.preset + b"\x00", 0)

        key = secrets.token_bytes(16)
        nonce = secrets.token_hex(3)
        for radio in (peer, kit):
            slot = empty_slot(radio)
            radio.slot = slot

            def remove_channel(device, index):
                device.set_channel(index, b"", bytes(16))
                channel = device.get_channel(index)
                require(channel[2] == 0 and not any(channel[34:]), "Temporary channel was not removed")

            cleanup.callback(remove_channel, radio, slot)
            radio.set_channel(slot, b"Zygis kit test", key)

        def restore_binding():
            command = "status channel clear" if kit_binding == 255 else f"status channel {kit_binding}"
            require(kit.cli(command).startswith("Status channel:"), "Kit tracking binding could not be restored")
            require(int(kit.state()[2]) == kit_binding, "Kit binding did not restore")

        cleanup.callback(restore_binding)
        require(kit.cli(f"status channel {kit.slot}").startswith("Status channel:"), "Temporary binding failed")
        require(kit.cli("verify").startswith("READY:"), "Temporary kit binding failed verification")
        if on_kit_message is not None:
            on_kit_message(kit, False)
        for sender, receiver in ((peer, kit), (kit, peer)):
            message = f"Žygis kit test {nonce}"
            sender.send(message)
            wait_message(receiver, sender, lambda body: body == message, "exact UTF-8 channel message")
            if receiver is kit and on_kit_message is not None:
                on_kit_message(kit, True)
        print("PASS two-way exact UTF-8 channel messaging", flush=True)

        exchange(peer, kit, "!power", lambda body: body.startswith("Power saving "))
        print("PASS !power reply", flush=True)
        exchange(peer, kit, "!kur", "!kur", ack=True)
        wait_message(peer, kit, status_report, "position or no-fix status")
        print("PASS !kur route ACK and status report", flush=True)
        exchange(peer, kit, "!triangulate", "!triangulate", ack=True)
        wait_message(peer, kit, lambda body: body.startswith("!triangulate: "), "discovery summary", timeout=35)
        print("PASS !triangulate route ACK and discovery summary", flush=True)
    print("Temporary channels removed. Original kit radio and tracking binding restored.", flush=True)
