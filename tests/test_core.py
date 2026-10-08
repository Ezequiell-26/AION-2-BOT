from core.decision import DecisionEngine
from core.models import Perception, PlayerStatus
from core.states import BotState

D = DecisionEngine()
KW = dict(low_hp_ratio=0.35, low_mp_ratio=0.18)

def test_low_hp_recovers():
    p = Perception(player=PlayerStatus(hp_ratio=0.2))
    assert D.next_state(p, **KW, has_target=True, combat_elapsed_s=1, combat_timeout_s=12) is BotState.RECOVERING

def test_no_target_targets():
    p = Perception(player=PlayerStatus())
    assert D.next_state(p, **KW, has_target=False, combat_elapsed_s=0, combat_timeout_s=12) is BotState.TARGETING

def test_combat_state():
    p = Perception(player=PlayerStatus(in_combat=True))
    assert D.next_state(p, **KW, has_target=True, combat_elapsed_s=2, combat_timeout_s=12) is BotState.COMBAT

def test_timeout_loots():
    p = Perception(player=PlayerStatus())
    assert D.next_state(p, **KW, has_target=True, combat_elapsed_s=12.1, combat_timeout_s=12) is BotState.LOOTING
