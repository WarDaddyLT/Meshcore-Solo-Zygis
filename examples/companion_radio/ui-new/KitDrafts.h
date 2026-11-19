#pragma once
// DraftCache adapted from AIDAS9 3134ba4e (KSK Lizdeika), MIT.
// See licenses/AIDAS9.txt.
#include <stdint.h>
#include <stddef.h>
#include <string.h>

namespace kit {
class DraftCache {
public:
  static const uint8_t CAPACITY = 4;
  static const uint16_t TEXT_LIMIT = 150;
  static const uint8_t KEY_SIZE = 32;

private:
  struct Slot {
    uint8_t key[KEY_SIZE];
    char text[TEXT_LIMIT + 1];
    uint16_t length;
    uint16_t cursor;
    uint16_t generation;
    bool valid;
  } _slots[CAPACITY] = {};
  uint16_t _generation = 0;

public:
  int8_t open(const uint8_t* key) {
    if (!key) return -1;
    int8_t empty = -1;
    uint8_t oldest = 0;
    for (uint8_t i = 0; i < CAPACITY; i++) {
      if (_slots[i].valid && memcmp(_slots[i].key, key, KEY_SIZE) == 0) {
        _slots[i].generation = ++_generation;
        return i;
      }
      if (!_slots[i].valid && empty < 0) empty = i;
      if (_slots[i].generation < _slots[oldest].generation) oldest = i;
    }
    uint8_t slot = empty >= 0 ? (uint8_t)empty : oldest;
    memset(&_slots[slot], 0, sizeof(_slots[slot]));
    memcpy(_slots[slot].key, key, KEY_SIZE);
    _slots[slot].valid = true;
    _slots[slot].generation = ++_generation;
    return slot;
  }

  bool load(int8_t slot, char* text, size_t capacity,
            uint16_t& length, uint16_t& cursor) const {
    if (slot < 0 || slot >= CAPACITY || !_slots[slot].valid ||
        !text || capacity <= _slots[slot].length) return false;
    memcpy(text, _slots[slot].text, _slots[slot].length + 1);
    length = _slots[slot].length;
    cursor = _slots[slot].cursor <= length ? _slots[slot].cursor : length;
    return true;
  }

  bool save(int8_t slot, const char* text, uint16_t length, uint16_t cursor) {
    if (slot < 0 || slot >= CAPACITY || !_slots[slot].valid || !text ||
        length > TEXT_LIMIT) return false;
    memcpy(_slots[slot].text, text, length);
    _slots[slot].text[length] = 0;
    _slots[slot].length = length;
    _slots[slot].cursor = cursor <= length ? cursor : length;
    _slots[slot].generation = ++_generation;
    return true;
  }

  void clear(int8_t slot) {
    if (slot >= 0 && slot < CAPACITY) memset(&_slots[slot], 0, sizeof(_slots[slot]));
  }
};

}  // namespace kit
