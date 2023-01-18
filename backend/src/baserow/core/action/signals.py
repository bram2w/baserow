from enum import Enum

from django.dispatch import Signal


class ActionCommandType(Enum):
    DO = "DO"
    UNDO = "UNDO"
    REDO = "REDO"


action_done = Signal()
