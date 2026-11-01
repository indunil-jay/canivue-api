from app.features.appointments.domain.enums.appointment_status import AppointmentStatus

OWNER_ALLOWED = {AppointmentStatus.CANCELLED}

SLOT_FREEING = {AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW}
