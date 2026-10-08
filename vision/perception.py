from __future__ import annotations
from dataclasses import dataclass
from core.models import Perception, PlayerStatus
from mss import MSS

@dataclass(slots=True)
class CaptureInfo:
    ok: bool
    width: int = 0
    height: int = 0

class PerceptionEngine:
    """Screen capture layer with conservative game-specific assumptions.

    AION 2 PC mode already supplies deterministic actions for target selection,
    basic attack, interaction and auto-potion. Semantic screen recognition is
    deliberately isolated for later calibration against a real client capture.
    """
    def __init__(self, monitor: int = 1) -> None:
        self.monitor = monitor
        self.last_capture = CaptureInfo(False)

    def capture_screen(self):
        try:
            with MSS() as sct:
                if self.monitor >= len(sct.monitors):
                    self.monitor = 1
                monitor = sct.monitors[self.monitor]
                frame = sct.grab(monitor)
                self.last_capture = CaptureInfo(True, frame.width, frame.height)
                return frame
        except Exception:
            self.last_capture = CaptureInfo(False)
            return None

    def scan(self) -> Perception:
        self.capture_screen()
        return Perception(player=PlayerStatus())
