#pragma once
#include <stdint.h>

// An event starts a five-second burst. Repeated events within a burst do not extend it.
class LedBlinkBurst {
  uint32_t started = 0;
  bool running = false;
public:
  void trigger(uint32_t now) {
    if (!running || (uint32_t)(now - started) >= 5000) {
      started = now;
      running = true;
    }
  }
  bool isActive(uint32_t now) const { return running && uint32_t(now - started) < 5000; }
  bool isOn(uint32_t now) {
    if (!running) return false;
    uint32_t elapsed = now - started;
    if (elapsed >= 5000) { running = false; return false; }
    return (elapsed / 250) % 2 == 0;
  }
};
