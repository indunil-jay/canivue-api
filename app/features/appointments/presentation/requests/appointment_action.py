from enum import Enum


class AppointmentAction(str, Enum):
    CONFIRM = "confirm"
    START = "start"
    COMPLETE = "complete"
    NO_SHOW = "no-show"
    CANCEL = "cancel"
