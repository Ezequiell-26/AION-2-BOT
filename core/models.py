from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass(slots=True)
class Target:
    id: str = "current"
    x: float = 0.0
    y: float = 0.0
    hp_ratio: float = 1.0
    distance_px: float = 0.0
    selected: bool = False

@dataclass(slots=True)
class PlayerStatus:
    hp_ratio: float = 1.0
    mp_ratio: float = 1.0
    in_combat: bool = False
    dead: bool = False

@dataclass(slots=True)
class Perception:
    player: PlayerStatus
    game_active: bool = False
    target: Optional[Target] = None
    target_seen: bool = False
    loot_available: bool = False
    blocked_ui: bool = False
    hud_ready: bool = False
    hp_bar_run: int = 0
    mp_bar_run: int = 0
    target_bar_run: int = 0
