from app.features.appointments.domain.entities.appointment import Appointment


def describe_time(appointment: Appointment) -> str:
    return appointment.date_time.strftime("%a %d %b at %H:%M UTC")
