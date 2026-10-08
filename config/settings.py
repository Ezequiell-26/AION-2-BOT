from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass(slots=True)
class Settings:
    game_window_title_contains: str = "AION 2"
    capture_monitor: int = 1
    dry_run: bool = True
    loop_delay_s: float = 0.12
    combat_timeout_s: float = 12.0
    loot_timeout_s: float = 3.0
    recovery_timeout_s: float = 10.0
    low_hp_ratio: float = 0.35
    low_mp_ratio: float = 0.18
    enable_auto_potion: bool = True
    auto_potion_key: str = "x"
    target_key: str = "tab"
    basic_attack_button: str = "left"
    interact_key: str = "f"
    movement_forward_key: str = "w"
    movement_left_key: str = "a"
    movement_right_key: str = "d"
    movement_back_key: str = "s"
    approach_pulse_s: float = 0.45
    attack_pulse_s: float = 0.70
    loot_pulses: int = 2
    loot_interval_s: float = 0.25
    skill_keys: list[str] | None = None
    skill_interval_s: float = 0.45
    rotation_enabled: bool = True
    patrol_enabled: bool = True
    patrol_side_every: int = 8
    hotkey_toggle: str = "f8"
    hotkey_exit: str = "f9"

    def __post_init__(self) -> None:
        if self.skill_keys is None:
            self.skill_keys = ["1", "2", "3", "4", "5", "6", "7", "8"]

    @classmethod
    def from_json(cls, path: Path) -> "Settings":
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(asdict(cls()), indent=2), encoding="utf-8")
            return cls()
        raw = json.loads(path.read_text(encoding="utf-8"))
        allowed = {field.name for field in cls.__dataclass_fields__.values()}
        values = {k: v for k, v in raw.items() if k in allowed}
        return cls(**values)
