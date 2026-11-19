"""Build only the ES8311 and nRF52 bus support from the pinned kit driver.

Unrelated touch drivers use std::mutex, which the bare-metal nRF toolchain does
not provide. Keeping them out also avoids compiling unused chip drivers.
"""
Import("env")

AUDIO_SOURCES = {
    "bus/bus_base.cpp",
    "chip/chip_base.cpp",
    "chip/i2c_i2s/es8311.cpp",
    "chip/i2c/tca8418.cpp",
    "core/logger.cpp",
    "platform/arduino_nrf/platform_hal.cpp",
    "platform/arduino_nrf/hardware_i2c.cpp",
    "platform/arduino_nrf/hardware_i2s.cpp",
}


def audio_sources_only(node):
    path = node.srcnode().get_abspath().replace("\\", "/")
    marker = "/cpp_bus_driver/src/"
    if marker in path and path.split(marker, 1)[1] not in AUDIO_SOURCES:
        return None
    return node


env.AddBuildMiddleware(audio_sources_only)
