from enum import Enum


class CursorState(Enum):
    PREVIOUS = "prev"
    NEXT = "next"


PREVIOUS_PREFIX = CursorState.PREVIOUS.value + "___"
NEXT_PREFIX = CursorState.NEXT.value + "___"
