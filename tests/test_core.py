from core.decision import DecisionEngine
from core.models import Perception, PlayerStatus
from core.states import BotState

D = DecisionEngine()
KW = dict(
    low_hp_ratio=0.35,
    low_mp_ratio=0.18,
    resume_hp_ratio=0.82,
    resume_mp_ratio=0.60,
)

def p(**kwargs):
    base = dict(hud_ready=True, blocked_ui=False, player=PlayerStatus())
    base["player"] = PlayerStatus(**kwargs)
    return Perception(**base)

def test_low_hp_recovers():
    assert D.next_state(
        p(hp_ratio=0.20), **KW, has_target=True, target_seen=True,
        target_hp_ratio=0.8, loot_ready=False, recovering=False,
        needs_approach=False, combat_elapsed_s=1, combat_timeout_s=20,
    ) is BotState.RECOVERING

def test_no_target_targets():
    assert D.next_state(
        p(), **KW, has_target=False, target_seen=False,
        target_hp_ratio=None, loot_ready=False, recovering=False,
        needs_approach=False, combat_elapsed_s=0, combat_timeout_s=20,
    ) is BotState.TARGETING

def test_target_combat():
    assert D.next_state(
        p(), **KW, has_target=True, target_seen=True,
        target_hp_ratio=0.8, loot_ready=False, recovering=False,
        needs_approach=False, combat_elapsed_s=2, combat_timeout_s=20,
    ) is BotState.COMBAT

def test_no_damage_approaches():
    assert D.next_state(
        p(), **KW, has_target=True, target_seen=True,
        target_hp_ratio=0.9, loot_ready=False, recovering=False,
        needs_approach=True, combat_elapsed_s=2, combat_timeout_s=20,
    ) is BotState.MOVING

def test_target_loss_loots():
    assert D.next_state(
        p(), **KW, has_target=True, target_seen=False,
        target_hp_ratio=None, loot_ready=True, recovering=False,
        needs_approach=False, combat_elapsed_s=4, combat_timeout_s=20,
    ) is BotState.LOOTING

def test_blocked_ui_never_attacks():
    blocked = Perception(player=PlayerStatus(), blocked_ui=True, hud_ready=False)
    assert D.next_state(
        blocked, **KW, has_target=True, target_seen=True,
        target_hp_ratio=0.8, loot_ready=False, recovering=False,
        needs_approach=False, combat_elapsed_s=1, combat_timeout_s=20,
    ) is BotState.BLOCKED_UI

def test_missing_target_retargets_after_timeout():
    assert D.next_state(
        p(), **KW, has_target=True, target_seen=False,
        target_hp_ratio=None, loot_ready=False, recovering=False,
        needs_approach=False, combat_elapsed_s=21, combat_timeout_s=20,
    ) is BotState.TARGETING
