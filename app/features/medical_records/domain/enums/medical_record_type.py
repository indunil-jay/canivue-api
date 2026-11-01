from enum import Enum


class MedicalRecordType(str, Enum):
    DIAGNOSIS = "diagnosis"
    PRESCRIPTION = "prescription"
    LAB_RESULT = "labResult"
    NOTE = "note"
    DOCUMENT = "document"
