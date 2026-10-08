from __future__ import annotations
import ctypes
import time
from dataclasses import dataclass

from mss import MSS
from core.models import Perception, PlayerStatus, Target

@dataclass(slots=True)
class CaptureInfo:
    ok: bool
    width: int = 0
    height: int = 0

class PerceptionEngine:
    """Low-cost screen perception with temporal debouncing and scale-aware regions."""

    REFERENCE_SIZE = (1360, 768)
    PLAYER_HP_REGION = (450, 665, 670, 681)
    PLAYER_MP_REGION = (680, 665, 920, 681)
    TARGET_HP_REGION = (525, 42, 820, 60)

    PLAYER_HP_BAR_MAX_RUN = 179
    PLAYER_MP_BAR_MAX_RUN = 199
    TARGET_BAR_MAX_RUN = 260

    MIN_TARGET_RUN = 15
    MIN_HUD_HP_RUN = 12
    MIN_HUD_MP_RUN = 6

    HUD_GRACE_S = 0.45
    TARGET_CONFIRM_CYCLES = 2
    TARGET_LOSS_GRACE_CYCLES = 2

    def __init__(self, monitor: int = 1, game_title_contains: str = "AION 2") -> None:
        self.monitor = monitor
        self.game_title_contains = game_title_contains.casefold()
        self.last_capture = CaptureInfo(False)
        self._sct = MSS()

        self._last_hud_good_at = 0.0
        self._last_hp_ratio = 1.0
        self._last_mp_ratio = 1.0
        self._target_streak = 0
        self._target_miss_streak = 0
        self._last_target_ratio: float | None = None

    def close(self) -> None:
        try:
            self._sct.close()
        except Exception:
            pass

    def game_window_active(self) -> bool:
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return False
            buf = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(hwnd, buf, len(buf))
            return self.game_title_contains in buf.value.casefold()
        except Exception:
            return False

    @staticmethod
    def _longest_run(frame, box: tuple[int, int, int, int], predicate) -> int:
        x0, y0, x1, y1 = box
        width = frame.width
        rgb = frame.rgb
        best = 0
        for y in range(max(0, y0), min(y1, frame.height)):
            cur = 0
            row = y * width * 3
            for x in range(max(0, x0), min(x1, width)):
                i = row + x * 3
                r, g, b = rgb[i], rgb[i + 1], rgb[i + 2]
                if predicate(r, g, b):
                    cur += 1
                    best = max(best, cur)
                else:
                    cur = 0
        return best

    @staticmethod
    def _red(r: int, g: int, b: int) -> bool:
        return r > 105 and r > g * 1.30 and r > b * 1.18

    @staticmethod
    def _cyan(r: int, g: int, b: int) -> bool:
        return g > 65 and b > 65 and (g + b) > (r * 2.0) and b > r * 1.08

    def _scaled_box(self, monitor: dict, ref: tuple[int, int, int, int]) -> dict:
        rw, rh = self.REFERENCE_SIZE
        sx = monitor["width"] / rw
        sy = monitor["height"] / rh
        x0, y0, x1, y1 = ref
        return {
            "left": monitor["left"] + int(x0 * sx),
            "top": monitor["top"] + int(y0 * sy),
            "width": max(1, int((x1 - x0) * sx)),
            "height": max(1, int((y1 - y0) * sy)),
        }

    @staticmethod
    def _ema(previous: float, current: float, alpha: float = 0.45) -> float:
        return previous + (current - previous) * alpha

    def scan(self) -> Perception:
        now = time.monotonic()
        if not self.game_window_active():
            self._target_streak = 0
            self._target_miss_streak = 0
            return Perception(
                player=PlayerStatus(
                    hp_ratio=self._last_hp_ratio,
                    mp_ratio=self._last_mp_ratio,
                ),
                game_active=False,
                blocked_ui=True,
                hud_ready=False,
            )

        try:
            monitor = self._sct.monitors[self.monitor]
            hp_mp = self._sct.grab(self._scaled_box(
                monitor,
                (
                    self.PLAYER_HP_REGION[0],
                    self.PLAYER_HP_REGION[1],
                    self.PLAYER_MP_REGION[2],
                    self.PLAYER_HP_REGION[3],
                ),
            ))
            target = self._sct.grab(self._scaled_box(monitor, self.TARGET_HP_REGION))
            self.last_capture = CaptureInfo(True, monitor["width"], monitor["height"])
        except Exception:
            self.last_capture = CaptureInfo(False)
            return Perception(
                player=PlayerStatus(
                    hp_ratio=self._last_hp_ratio,
                    mp_ratio=self._last_mp_ratio,
                ),
                game_active=True,
                blocked_ui=True,
                hud_ready=False,
            )

        hp_box = (
            0,
            0,
            self.PLAYER_HP_REGION[2] - self.PLAYER_HP_REGION[0],
            hp_mp.height,
        )
        mp_box = (
            self.PLAYER_MP_REGION[0] - self.PLAYER_HP_REGION[0],
            0,
            self.PLAYER_MP_REGION[2] - self.PLAYER_HP_REGION[0],
            hp_mp.height,
        )
        target_box = (
            0,
            0,
            self.TARGET_HP_REGION[2] - self.TARGET_HP_REGION[0],
            self.TARGET_HP_REGION[3] - self.TARGET_HP_REGION[1],
        )

        hp_run = self._longest_run(hp_mp, hp_box, self._red)
        mp_run = self._longest_run(hp_mp, mp_box, self._cyan)
        target_run = self._longest_run(target, target_box, self._red)

        raw_hp = min(1.0, hp_run / self.PLAYER_HP_BAR_MAX_RUN)
        raw_mp = min(1.0, mp_run / self.PLAYER_MP_BAR_MAX_RUN)

        hp_signal = hp_run >= self.MIN_HUD_HP_RUN
        mp_signal = mp_run >= self.MIN_HUD_MP_RUN
        hud_signal = hp_signal or mp_signal

        if hud_signal:
            self._last_hud_good_at = now
            self._last_hp_ratio = self._ema(self._last_hp_ratio, raw_hp)
            self._last_mp_ratio = self._ema(self._last_mp_ratio, raw_mp)

        hud_ready = hud_signal or (now - self._last_hud_good_at <= self.HUD_GRACE_S)
        if not hud_ready:
            self._target_streak = 0
            self._target_miss_streak = 0

        target_signal = target_run >= self.MIN_TARGET_RUN
        if target_signal:
            self._target_streak += 1
            self._target_miss_streak = 0
        else:
            self._target_miss_streak += 1
            if self._target_streak < self.TARGET_CONFIRM_CYCLES:
                self._target_streak = 0

        target_seen = (
            self._target_streak >= self.TARGET_CONFIRM_CYCLES
            or (
                self._last_target_ratio is not None
                and self._target_miss_streak <= self.TARGET_LOSS_GRACE_CYCLES
            )
        )

        target_ratio = None
        target_obj = None
        if target_signal:
            target_ratio = min(1.0, target_run / self.TARGET_BAR_MAX_RUN)
            self._last_target_ratio = target_ratio
        elif target_seen:
            target_ratio = self._last_target_ratio

        if target_seen and target_ratio is not None:
            target_obj = Target(
                hp_ratio=target_ratio,
                selected=True,
            )
        elif self._target_miss_streak > self.TARGET_LOSS_GRACE_CYCLES:
            self._last_target_ratio = None

        return Perception(
            player=PlayerStatus(
                hp_ratio=self._last_hp_ratio,
                mp_ratio=self._last_mp_ratio,
                in_combat=target_seen,
            ),
            game_active=True,
            target=target_obj,
            target_seen=target_seen,
            blocked_ui=not hud_ready,
            hud_ready=hud_ready,
            hp_bar_run=hp_run,
            mp_bar_run=mp_run,
            target_bar_run=target_run,
        )
