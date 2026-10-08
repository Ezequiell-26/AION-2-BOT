from __future__ import annotations
import logging
import time
from pathlib import Path

from actions.controller import InputController
from config.settings import Settings
from core.decision import DecisionEngine
from core.states import BotState
from vision.perception import PerceptionEngine

class FarmingBot:
    def __init__(self, settings: Settings, log_path: Path | None = None) -> None:
        self.settings = settings
        self.vision = PerceptionEngine(settings.capture_monitor)
        self.input = InputController(settings.dry_run, settings.game_window_title_contains)
        self.decision = DecisionEngine()
        self.running = True
        self.enabled = False
        self._targeted = False
        self._target_seen_once = False
        self._target_lost_cycles = 0
        self._combat_started_at = 0.0
        self._last_damage_at = 0.0
        self._last_target_hp: float | None = None
        self._kills = 0
        self._cycles = 0
        self._patrol_counter = 0
        self._potion_armed = False
        self._last_ui_recovery = 0.0
        self.logger = logging.getLogger("aion2-farmer")
        if not self.logger.handlers and log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(log_path, encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def stop(self) -> None:
        self.running = False
        self.input.stop_movement(self._movement_keys())
        self.vision.close()

    def _movement_keys(self) -> tuple[str, ...]:
        s = self.settings
        return (s.movement_forward_key, s.movement_left_key, s.movement_right_key, s.movement_back_key)

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        self.logger.info("bot_enabled=%s", enabled)
        print(f"Bot {'RUNNING' if enabled else 'PAUSED'}")
        if not enabled:
            self.input.stop_movement(self._movement_keys())
            return
        self._targeted = False
        self._target_seen_once = False
        self._target_lost_cycles = 0
        self._combat_started_at = 0.0
        self._last_damage_at = time.monotonic()
        self._last_target_hp = None

    def run(self) -> None:
        self.logger.info("started dry_run=%s", self.settings.dry_run)
        print("AION 2 Farmer started")
        print(f"dry_run={self.settings.dry_run}")
        print(f"auto_potion={self.settings.enable_auto_potion} ({self.settings.auto_potion_key.upper()})")
        print(f"toggle={self.settings.hotkey_toggle.upper()} | exit={self.settings.hotkey_exit.upper()}")
        print("Bot is PAUSED. Press F8 to toggle, F9 to exit.")
        last_state = BotState.PAUSED

        try:
            while self.running:
                if not self.enabled:
                    time.sleep(0.20)
                    continue

                perception = self.vision.scan()
                now = time.monotonic()

                if (
                    self.settings.enable_auto_potion
                    and not self._potion_armed
                    and perception.hud_ready
                ):
                    self.input.press(self.settings.auto_potion_key)
                    self._potion_armed = True
                    self.logger.info("auto_potion_armed")

                target_hp = perception.target.hp_ratio if perception.target else None
                if target_hp is not None:
                    self._target_seen_once = True
                    self._target_lost_cycles = 0
                    if (
                        self._last_target_hp is not None
                        and target_hp < self._last_target_hp - 0.015
                    ):
                        self._last_damage_at = now
                    self._last_target_hp = target_hp
                elif self._targeted and self._target_seen_once:
                    self._target_lost_cycles += 1

                loot_ready = (
                    self._targeted
                    and self._target_seen_once
                    and self._target_lost_cycles >= 3
                )
                elapsed = 0.0 if self._combat_started_at == 0 else now - self._combat_started_at
                needs_approach = (
                    self._targeted
                    and self._target_seen_once
                    and perception.target_seen
                    and now - self._last_damage_at >= self.settings.no_damage_approach_s
                )

                state = self.decision.next_state(
                    perception,
                    low_hp_ratio=self.settings.low_hp_ratio,
                    low_mp_ratio=self.settings.low_mp_ratio,
                    resume_hp_ratio=self.settings.resume_hp_ratio,
                    resume_mp_ratio=self.settings.resume_mp_ratio,
                    has_target=self._targeted,
                    target_seen=perception.target_seen,
                    target_hp_ratio=target_hp,
                    loot_ready=loot_ready,
                    recovering=last_state is BotState.RECOVERING,
                    needs_approach=needs_approach,
                    combat_elapsed_s=elapsed,
                    combat_timeout_s=self.settings.combat_timeout_s,
                )
                if state != last_state:
                    self.logger.info(
                        "state=%s hp=%.3f mp=%.3f target=%s target_hp=%s",
                        state.name,
                        perception.player.hp_ratio,
                        perception.player.mp_ratio,
                        perception.target_seen,
                        None if target_hp is None else round(target_hp, 3),
                    )
                    last_state = state
                self._execute(state, perception)
                self._cycles += 1
                time.sleep(self.settings.loop_delay_s)
        finally:
            self.input.stop_movement(self._movement_keys())
            self.vision.close()
            self.logger.info("stopped cycles=%d kills=%d", self._cycles, self._kills)

    def _execute(self, state: BotState, perception) -> None:
        s = self.settings

        if state is BotState.BLOCKED_UI:
            self.input.stop_movement(self._movement_keys())
            now = time.monotonic()
            if now - self._last_ui_recovery >= s.ui_recovery_interval_s:
                self.input.press(s.escape_key)
                self._last_ui_recovery = now
            return

        if state is BotState.TARGETING:
            self.input.target_nearest(s.target_key)
            self._targeted = True
            self._target_seen_once = False
            self._target_lost_cycles = 0
            self._last_target_hp = None
            self._combat_started_at = time.monotonic()
            self._last_damage_at = self._combat_started_at
            return

        if state is BotState.MOVING:
            self.input.hold(s.movement_forward_key, s.approach_pulse_s)
            self._last_damage_at = time.monotonic()
            return

        if state is BotState.COMBAT:
            self.input.basic_attack(s.basic_attack_button)
            if s.rotation_enabled:
                for key in s.skill_keys or []:
                    if not self.running or not self.enabled:
                        break
                    self.input.press(key)
                    time.sleep(s.skill_interval_s if not s.dry_run else min(s.skill_interval_s, 0.02))
            return

        if state is BotState.LOOTING:
            for _ in range(max(1, s.loot_pulses)):
                self.input.press(s.interact_key)
                time.sleep(s.loot_interval_s if not s.dry_run else min(s.loot_interval_s, 0.02))
            self._targeted = False
            self._target_seen_once = False
            self._target_lost_cycles = 0
            self._combat_started_at = 0.0
            self._last_target_hp = None
            self._kills += 1
            self._patrol_counter += 1
            if s.patrol_enabled and self._patrol_counter >= max(1, s.patrol_side_every):
                self.input.hold(s.movement_right_key, 0.25)
                self._patrol_counter = 0
            return

        if state is BotState.RECOVERING:
            self.input.stop_movement(self._movement_keys())
            time.sleep(s.recovery_timeout_s if not s.dry_run else min(s.recovery_timeout_s, 0.05))
            self._targeted = False
            self._target_seen_once = False
            self._target_lost_cycles = 0
            self._combat_started_at = 0.0
            self._last_target_hp = None
            return
