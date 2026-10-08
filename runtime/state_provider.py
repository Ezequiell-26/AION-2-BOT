from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

@dataclass(slots=True)
class GameState:
    game_active: bool = False
    hud_ready: bool = False
    blocked_ui: bool = False
    hp_ratio: float = 0.0
    mp_ratio: float = 0.0
    target_id: str | None = None
    target_seen: bool = False
    target_hp_ratio: float | None = None
    target_distance: float | None = None
    in_combat: bool = False
    loot_available: bool = False
    dead: bool = False

class StateProvider(Protocol):
    def read(self) -> GameState: ...
    def close(self) -> None: ...
