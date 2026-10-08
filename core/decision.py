from __future__ import annotations
from core.models import Perception
from core.states import BotState

class DecisionEngine:
    def next_state(
        self,
        p: Perception,
        *,
        low_hp_ratio: float,
        low_mp_ratio: float,
        has_target: bool,
        combat_elapsed_s: float,
        combat_timeout_s: float,
        loot_hint: bool = False,
    ) -> BotState:
        if p.unexpected_window or p.stuck or p.player.dead:
            return BotState.RECOVERING
        if p.player.hp_ratio < low_hp_ratio or p.player.mp_ratio < low_mp_ratio:
            return BotState.RECOVERING
        if loot_hint or p.loot_available:
            return BotState.LOOTING
        if not has_target:
            return BotState.TARGETING
        if combat_elapsed_s >= combat_timeout_s:
            return BotState.LOOTING
        return BotState.COMBAT
