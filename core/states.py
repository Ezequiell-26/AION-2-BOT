from enum import Enum, auto

class BotState(Enum):
    SCANNING = auto()
    TARGETING = auto()
    MOVING = auto()
    COMBAT = auto()
    LOOTING = auto()
    RECOVERING = auto()
    PAUSED = auto()
    STOPPED = auto()
