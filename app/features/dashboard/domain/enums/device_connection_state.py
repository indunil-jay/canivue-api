from enum import Enum


class DeviceConnectionState(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    NOT_PAIRED = "notPaired"
