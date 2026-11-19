#pragma once
#include <stdint.h>

// A normal Up is dispatched after a short delay. Square may still lock during
// the rest of the window, including when an e-paper refresh delayed its poll.
class KitLockGesture {
  static constexpr uint32_t navDelayMs = 350;
  static constexpr uint32_t windowMs = 1600;
  uint32_t upAt = 0;
  bool armed = false;
  bool pendingUp = false;

public:
  bool pollUp(uint32_t now) {
    if (armed && uint32_t(now - upAt) >= windowMs) return cancel();
    if (!pendingUp || uint32_t(now - upAt) < navDelayMs) return false;
    pendingUp = false;
    return true;
  }

  bool cancel() {
    armed = false;
    const bool pending = pendingUp;
    pendingUp = false;
    return pending;
  }

  void up(uint32_t now) {
    upAt = now;
    armed = pendingUp = true;
  }

  bool square(uint32_t now) {
    const bool matched = armed && uint32_t(now - upAt) < windowMs;
    if (matched) cancel();
    return matched;
  }
};
