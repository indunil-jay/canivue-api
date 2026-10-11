"""Fill a development database with demo content.

    python -m tools.seed_demo

Creates a demo owner with three Dogs, three verified veterinarians, an administrator,
45 days of readings, care tasks, a paired collar, a confirmed appointment and community
posts. Safe to run twice: it does nothing once the demo owner exists.

Every demo account uses DEMO_PASSWORD, which is public, so this refuses to run when
APP_ENV is "production".
"""

import asyncio
import random
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.features.appointments.domain.entities.appointment import Appointment
from app.features.appointments.domain.enums.appointment_status import AppointmentStatus
from app.features.appointments.infrastructure.persistence.repositories.appointment_repository import (
    SqlAlchemyAppointmentRepository,
)
from app.features.auth.domain.entities.user import User
from app.features.auth.domain.enums.role import Role
from app.features.auth.infrastructure.persistence.repositories.user_repository import (
    SqlAlchemyUserRepository,
)
from app.features.auth.infrastructure.persistence.seed import seed_rbac_catalog
from app.features.auth.infrastructure.services.hasher import Argon2PasswordHasher
from app.features.community.domain.entities.community_post import CommunityPost
from app.features.community.infrastructure.persistence.repositories.community_repository import (
    SqlAlchemyCommunityRepository,
)
from app.features.community.infrastructure.persistence.seed import seed_communities
from app.features.devices.domain.entities.smart_collar import SmartCollar
from app.features.devices.infrastructure.persistence.repositories.smart_collar_repository import (
    SqlAlchemySmartCollarRepository,
)
from app.features.dogs.domain.entities.dog import Dog
from app.features.dogs.domain.enums.dog_sex import DogSex
from app.features.dogs.domain.value_objects.insurance import Insurance
from app.features.dogs.domain.value_objects.medication import Medication
from app.features.dogs.domain.value_objects.vaccination import Vaccination
from app.features.dogs.infrastructure.persistence.repositories.dog_repository import (
    SqlAlchemyDogRepository,
)
from app.features.health_metrics.domain.entities.metric_reading import MetricReading
from app.features.health_metrics.domain.enums.health_metric import HealthMetric
from app.features.health_metrics.infrastructure.persistence.repositories.metric_reading_repository import (
    SqlAlchemyMetricReadingRepository,
)
from app.features.preventive_care.domain.entities.care_task import CareTask
from app.features.preventive_care.domain.enums.care_task_category import CareTaskCategory
from app.features.preventive_care.infrastructure.persistence.repositories.care_task_repository import (
    SqlAlchemyCareTaskRepository,
)
from app.features.veterinarians.domain.entities.vet_profile import VetProfile
from app.features.veterinarians.domain.enums.consultation_type import ConsultationType
from app.features.veterinarians.infrastructure.persistence.repositories.vet_profile_repository import (
    SqlAlchemyVetProfileRepository,
)

DEMO_PASSWORD = "CanivueDemo123!"
OWNER_EMAIL = "owner@canivue.demo"
ADMIN_EMAIL = "admin@canivue.demo"
READING_DAYS = 45

# (email, name, specialty, years, fee, clinic, consultation types)
VETS = [
    ("sarah@canivue.demo", "Dr. Sarah Jenkins", "Dermatology", 12, 45.0, "Bay Area Vet",
     ("video", "inPerson", "chat")),
    ("robert@canivue.demo", "Dr. Robert Miller", "Orthopedics", 9, 55.0, "Sunset Animal Clinic",
     ("video", "inPerson")),
    ("priya@canivue.demo", "Dr. Priya Nair", "Internal Medicine", 15, 60.0, "Oakwood Vet",
     ("video", "chat")),
]  # fmt: skip

# metric -> (typical daily value, day-to-day spread)
TYPICAL = {
    HealthMetric.HEART_RATE: (88, 6),
    HealthMetric.ACTIVITY: (7200, 1500),
    HealthMetric.SLEEP: (12.5, 1.0),
    HealthMetric.TEMPERATURE: (38.6, 0.2),
    HealthMetric.HYDRATION: (1300, 200),
}


def _dogs(owner_id: int, today: date) -> list[Dog]:
    def ago(days: int) -> date:
        return today - timedelta(days=days)

    return [
        Dog(
            owner_id=owner_id, name="Buddy", breed="Golden Retriever",
            birth_date=ago(3 * 365 + 60), gender=DogSex.MALE, weight_kg=28.5,
            color="Golden Honey", microchip_id="985141002348123", avatar_emoji="🐕",
            is_neutered=True, blood_group="DEA 1.1+", allergies=["Wheat (mild)"],
            primary_vet="Dr. Sarah Jenkins (Bay Area Vet)",
            special_notes="Active and energetic, loves swimming and retriever training.",
            existing_conditions=["Mild hip dysplasia (monitoring)"],
            vaccinations=[
                Vaccination("Rabies", ago(200), ago(200) + timedelta(days=365)),
                Vaccination("DHPP", ago(280), ago(280) + timedelta(days=365)),
            ],
            medications=[Medication("Joint Support Chews", "1 chew", "Daily")],
            insurance=Insurance("PetGuard Plus", "PG-88213", today + timedelta(days=240)),
        ),
        Dog(
            owner_id=owner_id, name="Luna", breed="German Shepherd",
            birth_date=ago(365 + 180), gender=DogSex.FEMALE, weight_kg=24.0,
            color="Black & Tan", microchip_id="985141009876543", is_neutered=True,
            blood_group="DEA 1.1-", primary_vet="Dr. Robert Miller (Sunset Animal Clinic)",
            special_notes="Highly intelligent, protective, in intermediate agility training.",
            vaccinations=[Vaccination("Rabies", ago(120), ago(120) + timedelta(days=365))],
        ),
        Dog(
            owner_id=owner_id, name="Charlie", breed="French Bulldog",
            birth_date=ago(2 * 365), gender=DogSex.MALE, weight_kg=12.2, color="Brindle",
            microchip_id="985141005544332", avatar_emoji="🐾", is_neutered=True,
            blood_group="DEA 1.2+", allergies=["Chicken protein"],
            primary_vet="Dr. Sarah Jenkins (Bay Area Vet)",
            special_notes="Prefers cool indoor spaces, sensitive respiratory system.",
            existing_conditions=["Brachycephalic airway syndrome (mild)"],
            vaccinations=[Vaccination("Rabies", ago(300), ago(300) + timedelta(days=365))],
            insurance=Insurance("Canivue Care", "CV-40217", today + timedelta(days=90)),
        ),
    ]  # fmt: skip


def _readings(dog: Dog, now: datetime) -> list[MetricReading]:
    rng = random.Random(dog.name)
    readings = []
    for day in range(READING_DAYS, 0, -1):
        at = (now - timedelta(days=day)).replace(hour=12, minute=0, second=0, microsecond=0)
        for metric, (typical, spread) in TYPICAL.items():
            value = round(max(0.0, rng.gauss(typical, spread)), 1)
            readings.append(
                MetricReading(dog_id=dog.id, metric=metric, value=value, recorded_at=at)
            )
        if day % 5 == 0:
            weight = round(dog.weight_kg + rng.uniform(-0.3, 0.3), 1)
            readings.append(
                MetricReading(
                    dog_id=dog.id, metric=HealthMetric.WEIGHT, value=weight, recorded_at=at
                )
            )
    return readings


def _next_weekday(now: datetime) -> datetime:
    slot = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    while slot.weekday() >= 5:
        slot += timedelta(days=1)
    return slot


async def seed_demo(session: AsyncSession) -> bool:
    """Seeds the demo content. Returns False when it was already there."""
    users = SqlAlchemyUserRepository(session=session)
    if await users.get_by_email(OWNER_EMAIL):
        return False

    await seed_rbac_catalog(session)
    await seed_communities(session)
    now = datetime.now(timezone.utc)
    hashed = Argon2PasswordHasher().hash(DEMO_PASSWORD)

    async def user(email: str, name: str, role: Role) -> User:
        return await users.create(
            User(id=None, email=email, hashed_password=hashed, role=role, full_name=name)
        )

    await user(ADMIN_EMAIL, "Demo Admin", Role.ADMIN)
    owner = await user(OWNER_EMAIL, "Alex Taylor", Role.CLIENT)

    vet_profiles = SqlAlchemyVetProfileRepository(session=session)
    profiles = []
    for email, name, specialty, years, fee, clinic, types in VETS:
        account = await user(email, name, Role.VET)
        profiles.append(
            await vet_profiles.create(
                VetProfile(
                    user_id=account.id, name=name, verified=True, specialty=specialty,
                    specialties=[specialty, "General Practice"], experience_years=years,
                    consultation_fee_usd=fee, response_time_minutes=30,
                    languages=["English"], consultation_types=list(types),
                    bio=f"{name} has practised {specialty.lower()} for {years} years.",
                    clinics=[clinic], qualifications=["DVM"],
                )
            )
        )  # fmt: skip

    dog_repo = SqlAlchemyDogRepository(session=session)
    reading_repo = SqlAlchemyMetricReadingRepository(session=session)
    dogs = []
    for dog in _dogs(owner.id, now.date()):
        dogs.append(await dog_repo.create(dog))
        await reading_repo.add_many(_readings(dogs[-1], now))
    buddy = dogs[0]

    tasks = SqlAlchemyCareTaskRepository(session=session)
    for category, title, days in [
        (CareTaskCategory.FLEA_TICK, "Flea & tick treatment", -2),
        (CareTaskCategory.VACCINATION, "DHPP booster", 12),
        (CareTaskCategory.GROOMING, "Nail trim", 20),
        (CareTaskCategory.ANNUAL_CHECK, "Annual health check", 60),
    ]:
        await tasks.create(
            CareTask(
                dog_id=buddy.id, category=category, title=title, due_date=now + timedelta(days=days)
            )
        )

    collar = SmartCollar(dog_id=buddy.id, firmware_version="3.2.1")
    collar.pair()
    collar.record_sync(records_synced=READING_DAYS * len(TYPICAL), battery_percent=82)
    await SqlAlchemySmartCollarRepository(session=session).save(collar)

    sarah = profiles[0]
    await SqlAlchemyAppointmentRepository(session=session).create(
        Appointment(
            owner_id=owner.id, owner_name=owner.full_name, vet_id=sarah.id,
            vet_user_id=sarah.user_id, vet_name=sarah.name, dog_id=buddy.id, dog_name=buddy.name,
            date_time=_next_weekday(now), status=AppointmentStatus.CONFIRMED,
            consultation_type=ConsultationType.VIDEO, fee_usd=sarah.consultation_fee_usd,
            notes="Follow-up on seasonal itching.",
        )
    )  # fmt: skip

    community = SqlAlchemyCommunityRepository(session)
    await community.add_post(
        CommunityPost(
            author_id=sarah.user_id, author_name=sarah.name, is_veterinarian=True,
            community_id="skin-allergies", community_tag="Skin Allergies",
            content="Seasonal itching often peaks in spring. Rinse paws after walks and "
            "see your vet if scratching breaks the skin.",
        )
    )  # fmt: skip
    await community.add_post(
        CommunityPost(
            author_id=owner.id, author_name=owner.full_name, community_id="arthritis",
            community_tag="Arthritis",
            content="Buddy's joint chews seem to be helping on our longer walks. "
            "Has anyone tried hydrotherapy?",
        )
    )  # fmt: skip
    await session.flush()
    return True


async def main() -> None:
    if settings.APP_ENV.lower() == "production":
        raise SystemExit("Refusing to seed demo accounts with a public password in production.")

    import app.main  # noqa: F401  (registers every model on Base.metadata)
    from app.core.database import AsyncSessionLocal, Base, engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        created = await seed_demo(session)
        await session.commit()
    await engine.dispose()

    if created:
        print(f"Demo data created. Sign in as {OWNER_EMAIL} (see DEMO_PASSWORD in this file).")
    else:
        print("Demo data is already present; nothing was changed.")


if __name__ == "__main__":
    asyncio.run(main())
