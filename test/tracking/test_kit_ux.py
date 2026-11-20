"""Check keypad timing and the T-Echo Lite carousel's monochrome assets."""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "examples/companion_radio/ui-new"

def test_gesture():
    source = """
#include <cassert>
#include "KitLockGesture.h"
int main() {
  KitLockGesture gesture;
  assert(!gesture.square(200));
  gesture.up(500);
  assert(!gesture.pollUp(849));
  assert(gesture.square(849));
  assert(!gesture.pollUp(850));
  gesture.up(1000);
  assert(gesture.pollUp(1350));
  assert(!gesture.pollUp(1351));
  assert(gesture.square(2599));
  gesture.up(3000);
  assert(gesture.pollUp(4600));
  assert(!gesture.square(4600));
  gesture.up(UINT32_MAX - 100);
  assert(gesture.square(130));
  gesture.up(10000);
  assert(gesture.cancel());
  assert(!gesture.square(10010));
}
"""
    with tempfile.TemporaryDirectory() as tmp:
        src, exe = Path(tmp) / "keys.cpp", Path(tmp) / "keys"
        src.write_text(source)
        subprocess.run(["c++", "-std=c++17", "-I", str(UI), str(src), "-o", str(exe)], check=True)
        subprocess.run([str(exe)], check=True)

def test_icons():
    icons = (UI / "KitCarouselIcons.h").read_text()
    per_page = {}
    for name, size, bits in re.findall(r"kitIcon_(\w+)_(32|48)\[\]\s*=\s*\{([^}]*)\}", icons):
        size = int(size)
        packed = bytes(int(v, 16) for v in re.findall(r"0x([\da-fA-F]+)", bits))
        assert len(packed) == size * (size // 8)
        assert len(set(packed)) > 4
        per_page.setdefault(name, set()).add(size)
    assert len(per_page) == 10
    assert all(sizes == {32, 48} for sizes in per_page.values())

def test_companion_read_state():
    core = (UI.parent / "ui-core/UiCore.h").read_text()
    method = re.search(r"  void onQueueSizeChanged\(.*?^  }", core, re.MULTILINE | re.DOTALL)[0]
    source = """
#include <cassert>
struct Queue {
  void markAllRead() { ++marks; }
  int _queue_len = 0;
  int marks = 0;
""" + method.replace(" override", "") + """
};
int main() {
  Queue queue;
  queue.onQueueSizeChanged(1);
  queue.onQueueSizeChanged(0);
  assert(queue._queue_len == 0);
#ifdef ZYGIS_KIT_UX
  assert(queue.marks == 0);
#else
  assert(queue.marks == 1);
#endif
}
"""
    with tempfile.TemporaryDirectory() as tmp:
        src, exe = Path(tmp) / "unread.cpp", Path(tmp) / "unread"
        src.write_text(source)
        for flags in ([], ["-DZYGIS_KIT_UX"]):
            subprocess.run(["c++", "-std=c++17", *flags, str(src), "-o", str(exe)], check=True)
            subprocess.run([str(exe)], check=True)


if __name__ == "__main__":
    test_gesture()
    test_icons()
    test_companion_read_state()
    print("Kit keypad timing, monochrome icons and local unread state passed")
