from __future__ import annotations
import ctypes
import time
from ctypes import wintypes
from typing import Literal

MouseButton = Literal["left", "right", "middle"]

user32 = ctypes.windll.user32 if hasattr(ctypes, "windll") else None

INPUT_KEYBOARD = 1
INPUT_MOUSE = 0
KEYEVENTF_KEYUP = 0x0002
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040

SPECIAL_KEYS = {
    "backspace": 0x08,
    "tab": 0x09,
    "enter": 0x0D,
    "shift": 0x10,
    "ctrl": 0x11,
    "alt": 0x12,
    "pause": 0x13,
    "capslock": 0x14,
    "esc": 0x1B,
    "space": 0x20,
    "pageup": 0x21,
    "pagedown": 0x22,
    "end": 0x23,
    "home": 0x24,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
    "insert": 0x2D,
    "delete": 0x2E,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
    "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
    "num": 0x90,
}

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", wintypes.ULONG_PTR if hasattr(wintypes, "ULONG_PTR") else wintypes.LPVOID),
    ]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", wintypes.ULONG_PTR if hasattr(wintypes, "ULONG_PTR") else wintypes.LPVOID),
    ]

class INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]

class INPUT(ctypes.Structure):
    _anonymous_ = ("data",)
    _fields_ = [("type", wintypes.DWORD), ("data", INPUT_UNION)]

class InputController:
    """Low-dependency Windows input adapter using native SendInput."""
    def __init__(self, dry_run: bool = True, game_title_contains: str = "AION 2") -> None:
        self.dry_run = dry_run
        self.game_title_contains = game_title_contains.casefold()
        if not dry_run and user32 is None:
            raise RuntimeError("Native Windows input is only available on Windows.")

    @staticmethod
    def _vk(key: str) -> int:
        normalized = key.strip().casefold()
        if normalized in SPECIAL_KEYS:
            return SPECIAL_KEYS[normalized]
        if len(normalized) == 1 and normalized.isalnum():
            return ord(normalized.upper())
        if normalized.startswith("f") and normalized[1:].isdigit():
            num = int(normalized[1:])
            if 1 <= num <= 24:
                return 0x70 + num - 1
        raise ValueError(f"Unsupported key: {key!r}")

    def game_window_active(self) -> bool:
        if self.dry_run:
            return True
        assert user32 is not None
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return False
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, buf, len(buf))
        return self.game_title_contains in buf.value.casefold()

    def _send_keyboard(self, key: str, key_up: bool = False) -> None:
        assert user32 is not None
        inp = INPUT(type=INPUT_KEYBOARD)
        inp.ki = KEYBDINPUT(
            wVk=self._vk(key),
            wScan=0,
            dwFlags=KEYEVENTF_KEYUP if key_up else 0,
            time=0,
            dwExtraInfo=0,
        )
        sent = user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        if sent != 1:
            raise OSError(f"SendInput keyboard failed for {key!r}")

    def press(self, key: str) -> None:
        if self.dry_run:
            print(f"[DRY] key {key}")
            return
        if not self.game_window_active():
            return
        self._send_keyboard(key, False)
        self._send_keyboard(key, True)

    def click(self, button: MouseButton = "left") -> None:
        if self.dry_run:
            print(f"[DRY] click {button}")
            return
        if not self.game_window_active():
            return
        flags = {
            "left": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP),
            "right": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP),
            "middle": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP),
        }[button]
        assert user32 is not None
        for flag in flags:
            inp = INPUT(type=INPUT_MOUSE)
            inp.mi = MOUSEINPUT(dx=0, dy=0, mouseData=0, dwFlags=flag, time=0, dwExtraInfo=0)
            sent = user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
            if sent != 1:
                raise OSError(f"SendInput mouse failed for {button!r}")

    def hold(self, key: str, seconds: float) -> None:
        if self.dry_run:
            print(f"[DRY] hold {key} {seconds:.2f}s")
            time.sleep(min(seconds, 0.05))
            return
        if not self.game_window_active():
            return
        self._send_keyboard(key, False)
        try:
            time.sleep(max(0.0, seconds))
        finally:
            self._send_keyboard(key, True)

    def stop_movement(self, keys: tuple[str, ...]) -> None:
        if self.dry_run or user32 is None:
            return
        for key in keys:
            try:
                if self.game_window_active():
                    self._send_keyboard(key, True)
            except Exception:
                pass

    def target_nearest(self, key: str) -> None:
        self.press(key)

    def basic_attack(self, button: MouseButton) -> None:
        self.click(button)
