from __future__ import annotations
from dataclasses import replace
from core.models import Perception
from runtime.state_provider import GameState, StateProvider
from vision.perception import PerceptionEngine

class VisualStateProvider:
    """StateProvider backed by the calibrated screen perception layer."""
    def __init__(self, perception: PerceptionEngine) -> None:
        self.perception = perception

    def read(self) -> GameState:
        p = self.perception.scan()
        return GameState(
            game_active=self.perception.game_window_active(),
            hud_ready=p.hud_ready,
            blocked_ui=p.blocked_ui,
            hp_ratio=p.player.hp_ratio,
            mp_ratio=p.player.mp_ratio,
            target_id=p.target.id if p.target else None,
            target_seen=p.target_seen,
            target_hp_ratio=p.target.hp_ratio if p.target else None,
            target_distance=p.target.distance_px if p.target else None,
            in_combat=p.player.in_combat,
            loot_available=p.loot_available,
            dead=p.player.dead,
        )

    def close(self) -> None:
        self.perception.close()

class SimulatedStateProvider:
    """Deterministic provider used for tests and development."""
    def __init__(self, states: list[GameState] | None = None) -> None:
        self.states = states or [GameState(game_active=True, hud_ready=True, hp_ratio=1.0, mp_ratio=1.0)]
        self.index = 0

    def read(self) -> GameState:
        state = self.states[min(self.index, len(self.states) - 1)]
        self.index += 1
        return replace(state)

    def close(self) -> None:
        pass
