"""Defines the enum for the friendship status codes"""

from enum import Enum


class FriendshipStatusCode(Enum):
    REQUESTED = "R"
    ACCEPTED = "A"
    DECLINED = "D"
    BLOCKED = "B"
