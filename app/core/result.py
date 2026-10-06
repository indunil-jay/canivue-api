from dataclasses import dataclass
from typing import Generic, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True)
class Success(Generic[T]):
    value: T
    is_success: bool = True
    is_failure: bool = False


@dataclass(frozen=True)
class Failure(Generic[E]):
    error: E
    is_success: bool = False
    is_failure: bool = True


Result = Union[Success[T], Failure[E]]


def Ok(value: T) -> Success[T]:
    return Success(value=value)


def Err(error: E) -> Failure[E]:
    return Failure(error=error)
