from enum import Enum


class Role(str, Enum):
    ADMIN = "ADMIN"
    VET = "VET"
    CLIENT = "CLIENT"
