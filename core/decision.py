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
        resume_hp_ratio: float,
        resume_mp_ratio: float,
        has_target: bool,
        target_seen: bool,
        target_hp_ratio: float | None,
        loot_ready: bool,
        recovering: bool,
        needs_approach: bool,
        combat_elapsed_s: float,
        combat_timeout_s: float,
    ) -> BotState:
        if p.blocked_ui or not p.hud_ready:
            return BotState.BLOCKED_UI
        if p.player.dead or p.player.hp_ratio <= 0.02:
            return BotState.RECOVERING
        if recovering and (p.player.hp_ratio < resume_hp_ratio or p.player.mp_ratio < resume_mp_ratio):
            return BotState.RECOVERING
        if p.player.hp_ratio < low_hp_ratio or p.player.mp_ratio < low_mp_ratio:
            return BotState.RECOVERING
        if loot_ready or p.loot_available:
            return BotState.LOOTING
        if not has_target:
            return BotState.TARGETING
        if not target_seen:
            if combat_elapsed_s >= combat_timeout_s:
                return BotState.TARGETING
            return BotState.MOVING
        if target_hp_ratio is not None and target_hp_ratio <= 0.03:
            return BotState.LOOTING
        if combat_elapsed_s >= combat_timeout_s:
            return BotState.MOVING
        if needs_approach:
            return BotState.MOVING
        return BotState.COMBAT
