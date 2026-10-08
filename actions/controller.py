from __future__ import annotations
import time
from typing import Literal

MouseButton = Literal["left", "right", "middle"]

class InputController:
    """AION 2 PC input adapter. dry_run keeps every action simulated."""
    def __init__(self, dry_run: bool = True, game_title_contains: str = "AION 2") -> None:
        self.dry_run = dry_run
        self.game_title_contains = game_title_contains.casefold()
        self._pyautogui = None
        self._pygetwindow = None
        if not dry_run:
            import pyautogui
            import pygetwindow
            pyautogui.PAUSE = 0.03
            pyautogui.FAILSAFE = True
            self._pyautogui = pyautogui
            self._pygetwindow = pygetwindow

    def game_window_active(self) -> bool:
        if self.dry_run:
            return True
        assert self._pygetwindow is not None
        try:
            window = self._pygetwindow.getActiveWindow()
            title = (window.title if window else "").casefold()
            return bool(title) and self.game_title_contains in title
        except Exception:
            return False

    def _guard(self) -> bool:
        if self.dry_run:
            return True
        return self.game_window_active()

    def press(self, key: str) -> None:
        if self.dry_run:
            print(f"[DRY] key {key}")
            return
        if not self._guard():
            return
        assert self._pyautogui is not None
        self._pyautogui.press(key)

    def click(self, button: MouseButton = "left") -> None:
        if self.dry_run:
            print(f"[DRY] click {button}")
            return
        if not self._guard():
            return
        assert self._pyautogui is not None
        self._pyautogui.click(button=button)

    def hold(self, key: str, seconds: float) -> None:
        if self.dry_run:
            print(f"[DRY] hold {key} {seconds:.2f}s")
            time.sleep(min(seconds, 0.05))
            return
        if not self._guard():
            return
        assert self._pyautogui is not None
        self._pyautogui.keyDown(key)
        try:
            time.sleep(max(0.0, seconds))
        finally:
            self._pyautogui.keyUp(key)

    def stop_movement(self, keys: tuple[str, ...]) -> None:
        if self.dry_run:
            return
        assert self._pyautogui is not None
        for key in keys:
            try:
                self._pyautogui.keyUp(key)
            except Exception:
                pass

    def target_nearest(self, key: str) -> None:
        self.press(key)

    def basic_attack(self, button: MouseButton) -> None:
        self.click(button)
