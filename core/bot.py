from __future__ import annotations
import logging
import time
from pathlib import Path

from actions.controller import InputController
from config.settings import Settings
from core.decision import DecisionEngine
from core.models import Perception
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
        self._combat_started_at = 0.0
        self._kills = 0
        self._cycles = 0
        self._patrol_counter = 0
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

    def _movement_keys(self) -> tuple[str, ...]:
        s = self.settings
        return (s.movement_forward_key, s.movement_left_key, s.movement_right_key, s.movement_back_key)

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        self.logger.info("bot_enabled=%s", enabled)
        print(f"Bot {'RUNNING' if enabled else 'PAUSED'}")
        if enabled:
            self._targeted = False
            self._combat_started_at = 0.0
            if self.settings.enable_auto_potion:
                # X toggles AION 2's in-game auto-potion. Start with it OFF
                # in-game so this activation is deterministic.
                self.input.press(self.settings.auto_potion_key)
        else:
            self.input.stop_movement(self._movement_keys())

    def run(self) -> None:
        self.logger.info("started dry_run=%s", self.settings.dry_run)
        print("AION 2 Farmer started")
        print(f"dry_run={self.settings.dry_run}")
        print(f"auto_potion={self.settings.enable_auto_potion} ({self.settings.auto_potion_key.upper()})")
        print(f"toggle={self.settings.hotkey_toggle.upper()} | exit={self.settings.hotkey_exit.upper()}")
        print("Bot is PAUSED. Press F8 to toggle, F9 to exit.")
        last_state = BotState.PAUSED
        while self.running:
            if not self.enabled:
                time.sleep(0.20)
                continue
            perception = self.vision.scan()
            elapsed = 0.0 if self._combat_started_at == 0 else time.monotonic() - self._combat_started_at
            state = self.decision.next_state(
                perception,
                low_hp_ratio=self.settings.low_hp_ratio,
                low_mp_ratio=self.settings.low_mp_ratio,
                has_target=self._targeted,
                combat_elapsed_s=elapsed,
                combat_timeout_s=self.settings.combat_timeout_s,
            )
            if state != last_state:
                self.logger.info("state=%s", state.name)
                last_state = state
            self._execute(state)
            self._cycles += 1
            time.sleep(self.settings.loop_delay_s)
        self.logger.info("stopped cycles=%d kills=%d", self._cycles, self._kills)

    def _execute(self, state: BotState) -> None:
        s = self.settings
        if state is BotState.TARGETING:
            self.input.target_nearest(s.target_key)
            self.input.hold(s.movement_forward_key, s.approach_pulse_s)
            self._targeted = True
            self._combat_started_at = time.monotonic()
            return

        if state is BotState.COMBAT:
            self.input.basic_attack(s.basic_attack_button)
            if s.rotation_enabled:
                for key in s.skill_keys or []:
                    if not self.running or not self.enabled:
                        break
                    self.input.press(key)
                    time.sleep(s.skill_interval_s if not s.dry_run else min(s.skill_interval_s, 0.03))
            return

        if state is BotState.LOOTING:
            for _ in range(max(1, s.loot_pulses)):
                self.input.press(s.interact_key)
                time.sleep(s.loot_interval_s if not s.dry_run else min(s.loot_interval_s, 0.03))
            self._targeted = False
            self._combat_started_at = 0.0
            self._kills += 1
            self._patrol_counter += 1
            if s.patrol_enabled and self._patrol_counter >= max(1, s.patrol_side_every):
                self.input.hold(s.movement_right_key, 0.25)
                self._patrol_counter = 0
            return

        if state is BotState.RECOVERING:
            self.input.stop_movement(self._movement_keys())
            # Auto-potion stays enabled; do not toggle X repeatedly.
            time.sleep(s.recovery_timeout_s if not s.dry_run else min(s.recovery_timeout_s, 0.05))
            self._targeted = False
            self._combat_started_at = 0.0
            return

        if state is BotState.MOVING:
            self.input.hold(s.movement_forward_key, s.approach_pulse_s)
            return
