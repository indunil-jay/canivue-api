from enum import Enum


class CollarConnectionState(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    NOT_PAIRED = "notPaired"
    PAIRING = "pairing"
