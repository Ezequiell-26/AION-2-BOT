from __future__ import annotations
import ctypes
import sys
import threading
import time
from pathlib import Path

from config.settings import Settings
from core.bot import FarmingBot

def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

def _vk_for_hotkey(name: str) -> int | None:
    return {"f8": 0x77, "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B}.get(name.lower())

class WindowsHotkeys:
    def __init__(self, bot: FarmingBot, toggle: str, exit_key: str) -> None:
        self.bot = bot
        self.toggle_vk = _vk_for_hotkey(toggle)
        self.exit_vk = _vk_for_hotkey(exit_key)
        self._thread = threading.Thread(target=self._run, name="hotkeys", daemon=True)
        self._last: set[int] = set()

    def start(self) -> None:
        self._thread.start()

    def _down(self, vk: int | None) -> bool:
        if vk is None or sys.platform != "win32":
            return False
        return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)

    def _run(self) -> None:
        while self.bot.running:
            pressed = {vk for vk in (self.toggle_vk, self.exit_vk) if self._down(vk)}
            newly_pressed = pressed - self._last
            if self.toggle_vk is not None and self.toggle_vk in newly_pressed:
                self.bot.set_enabled(not self.bot.enabled)
            if self.exit_vk is not None and self.exit_vk in newly_pressed:
                self.bot.stop()
                return
            self._last = pressed
            time.sleep(0.05)

def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("This runtime is prepared for Windows 10/11.")
    root = project_root()
    settings = Settings.from_json(root / "config" / "config.local.json")
    bot = FarmingBot(settings, root / "logs" / "aion2-farmer.log")
    hotkeys = WindowsHotkeys(bot, settings.hotkey_toggle, settings.hotkey_exit)
    hotkeys.start()
    try:
        bot.run()
    except KeyboardInterrupt:
        bot.stop()

if __name__ == "__main__":
    main()
