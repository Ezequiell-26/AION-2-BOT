from __future__ import annotations
from runtime.state_provider import GameState
from core.states import BotState

class DecisionEngine:
    """Policy layer: converts observed game state into the next bot state."""
    def next_state(
        self,
        state: GameState,
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
        if not state.game_active or state.blocked_ui or not state.hud_ready:
            return BotState.BLOCKED_UI
        if state.dead or state.hp_ratio <= 0.02:
            return BotState.RECOVERING
        if recovering and (state.hp_ratio < resume_hp_ratio or state.mp_ratio < resume_mp_ratio):
            return BotState.RECOVERING
        if state.hp_ratio < low_hp_ratio or state.mp_ratio < low_mp_ratio:
            return BotState.RECOVERING
        if loot_ready or state.loot_available:
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
