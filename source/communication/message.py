"""Classes & variables used for representing messages from board."""

from enum import Enum
from collections import namedtuple

Datatuple = namedtuple("Datatuple", ["time", "type", "subtype", "content"], defaults=[None] * 4)


class MsgType(Enum):
    EVENT = b"E"  # External event
    STATE = b"S"  # State transition
    PRINT = b"P"  # User print
    HARDW = b"H"  # Hardware callback
    VARBL = b"V"  # Variable change
    WARNG = b"!"  # Warning
    ERROR = b"!!"  # Error
    STOPF = b"X"  # Stop framework
    ANLOG = b"A"  # Analog

    @classmethod
    def from_byte(cls, byte_value):
        """Get member given value byte"""
        for member in cls:
            if member.value == byte_value:
                return member
        return byte_value

    def get_subtype(self, subtype_char):
        """Get subtype name from character"""
        if subtype_char == "_":
            return None
        else:
            return {
                MsgType.VARBL: {
                    "g": "get",
                    "s": "user_set",
                    "a": "api_set",
                    "p": "print",
                    "t": "run_start",
                    "e": "run_end",
                },
                MsgType.EVENT: {
                    "i": "input",
                    "t": "timer",
                    "p": "publish",
                    "u": "user",
                    "a": "api",
                    "s": "sync",
                },
                MsgType.PRINT: {
                    "t": "task",
                    "a": "api",
                    "u": "user",
                },
            }[self][subtype_char]
