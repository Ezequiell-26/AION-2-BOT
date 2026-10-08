from core.decision import DecisionEngine
from core.models import Perception, PlayerStatus
from core.states import BotState
from runtime.providers import SimulatedStateProvider
from runtime.state_provider import GameState
from vision.perception import PerceptionEngine

D = DecisionEngine()
KW = dict(
    low_hp_ratio=0.35,
    low_mp_ratio=0.18,
    resume_hp_ratio=0.82,
    resume_mp_ratio=0.60,
)

def game(**kwargs):
    base = dict(game_active=True, hud_ready=True, blocked_ui=False, hp_ratio=1.0, mp_ratio=1.0)
    base.update(kwargs)
    return GameState(**base)

def test_low_hp_recovers():
    assert D.next_state(
        game(hp_ratio=0.20), **KW, has_target=True, target_seen=True,
        target_hp_ratio=0.8, loot_ready=False, recovering=False,
        needs_approach=False, combat_elapsed_s=1, combat_timeout_s=20,
    ) is BotState.RECOVERING

def test_no_target_targets():
    assert D.next_state(
        game(), **KW, has_target=False, target_seen=False,
        target_hp_ratio=None, loot_ready=False, recovering=False,
        needs_approach=False, combat_elapsed_s=0, combat_timeout_s=20,
    ) is BotState.TARGETING

def test_target_combat():
    assert D.next_state(
        game(), **KW, has_target=True, target_seen=True,
        target_hp_ratio=0.8, loot_ready=False, recovering=False,
        needs_approach=False, combat_elapsed_s=2, combat_timeout_s=20,
    ) is BotState.COMBAT

def test_no_damage_approaches():
    assert D.next_state(
        game(), **KW, has_target=True, target_seen=True,
        target_hp_ratio=0.9, loot_ready=False, recovering=False,
        needs_approach=True, combat_elapsed_s=2, combat_timeout_s=20,
    ) is BotState.MOVING

def test_target_loss_loots():
    assert D.next_state(
        game(), **KW, has_target=True, target_seen=False,
        target_hp_ratio=None, loot_ready=True, recovering=False,
        needs_approach=False, combat_elapsed_s=4, combat_timeout_s=20,
    ) is BotState.LOOTING

def test_blocked_ui_never_attacks():
    assert D.next_state(
        game(blocked_ui=True, hud_ready=False), **KW, has_target=True, target_seen=True,
        target_hp_ratio=0.8, loot_ready=False, recovering=False,
        needs_approach=False, combat_elapsed_s=1, combat_timeout_s=20,
    ) is BotState.BLOCKED_UI

def test_missing_target_retargets_after_timeout():
    assert D.next_state(
        game(), **KW, has_target=True, target_seen=False,
        target_hp_ratio=None, loot_ready=False, recovering=False,
        needs_approach=False, combat_elapsed_s=21, combat_timeout_s=20,
    ) is BotState.TARGETING

def test_simulated_provider_is_deterministic():
    provider = SimulatedStateProvider([
        game(target_seen=True, target_hp_ratio=0.7),
        game(target_seen=False),
    ])
    assert provider.read().target_hp_ratio == 0.7
    assert provider.read().target_seen is False


def test_perception_longest_run_counts_single_pixel_steps():
    class Frame:
        width = 10
        height = 1
        rgb = bytes([220, 20, 20] * 5 + [20, 20, 20] * 5)

    assert PerceptionEngine._longest_run(Frame(), (0, 0, 10, 1), PerceptionEngine._red) == 5


def test_perception_ema_smooths_transient_value():
    assert round(PerceptionEngine._ema(1.0, 0.0, 0.45), 2) == 0.55
