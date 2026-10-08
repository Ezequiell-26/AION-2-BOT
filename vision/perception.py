from __future__ import annotations
from dataclasses import dataclass
from mss import MSS
from core.models import Perception, PlayerStatus, Target

@dataclass(slots=True)
class CaptureInfo:
    ok: bool
    width: int = 0
    height: int = 0

class PerceptionEngine:
    """Low-cost HUD perception calibrated for the current 1360x768 AION 2 layout."""
    PLAYER_HP_REGION = (450, 665, 670, 681)
    PLAYER_MP_REGION = (680, 665, 920, 681)
    TARGET_HP_REGION = (525, 42, 820, 60)
    PLAYER_BAR_MAX_RUN = 179
    TARGET_BAR_MAX_RUN = 260
    MIN_TARGET_RUN = 15
    MIN_HUD_RUN = 25

    def __init__(self, monitor: int = 1) -> None:
        self.monitor = monitor
        self.last_capture = CaptureInfo(False)
        self._sct = MSS()

    def close(self) -> None:
        try:
            self._sct.close()
        except Exception:
            pass

    @staticmethod
    def _longest_red_run(frame, box: tuple[int, int, int, int]) -> int:
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
                ok = r > 110 and r > g * 1.35 and r > b * 1.20
                if ok:
                    cur += 1
                    if cur > best:
                        best = cur
                else:
                    cur = 0
        return best

    def scan(self) -> Perception:
        try:
            frame = self._sct.grab(self._sct.monitors[self.monitor])
            self.last_capture = CaptureInfo(True, frame.width, frame.height)
        except Exception:
            self.last_capture = CaptureInfo(False)
            return Perception(player=PlayerStatus(), blocked_ui=True, hud_ready=False)

        hp_run = self._longest_red_run(frame, self.PLAYER_HP_REGION)
        mp_run = self._longest_red_run(frame, self.PLAYER_MP_REGION)
        target_run = self._longest_red_run(frame, self.TARGET_HP_REGION)

        hud_ready = hp_run >= self.MIN_HUD_RUN and mp_run >= self.MIN_HUD_RUN
        hp_ratio = min(1.0, hp_run / self.PLAYER_BAR_MAX_RUN)
        mp_ratio = min(1.0, mp_run / self.PLAYER_BAR_MAX_RUN)
        target_seen = target_run >= self.MIN_TARGET_RUN
        target = Target(hp_ratio=min(1.0, target_run / self.TARGET_BAR_MAX_RUN), selected=True) if target_seen else None

        return Perception(
            player=PlayerStatus(hp_ratio=hp_ratio, mp_ratio=mp_ratio, in_combat=target_seen),
            target=target,
            target_seen=target_seen,
            blocked_ui=not hud_ready,
            hud_ready=hud_ready,
            hp_bar_run=hp_run,
            mp_bar_run=mp_run,
            target_bar_run=target_run,
        )
