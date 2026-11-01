from datetime import date

from app.features.dogs.domain.entities.dog import Dog
from app.features.dogs.domain.exceptions import InvalidDogError


def validate_dog(dog: Dog) -> None:
    if not dog.name.strip():
        raise InvalidDogError("A Dog needs a name.")
    if dog.birth_date > date.today():
        raise InvalidDogError("Birth date cannot be in the future.")
