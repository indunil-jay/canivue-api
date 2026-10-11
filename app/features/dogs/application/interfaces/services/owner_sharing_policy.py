from typing import Protocol


class OwnerSharingPolicyProtocol(Protocol):
    """Whether an owner lets veterinarians see their Dogs' data (a privacy setting)."""

    async def shares_with_vets(self, owner_id: int) -> bool: ...
