from app.features.community.application.commands.toggle_membership.toggle_membership_command import (
    ToggleMembershipCommand,
)
from app.features.community.application.dtos.community_view import CommunityView
from app.features.community.application.interfaces.repositories.community_repository import (
    CommunityRepositoryProtocol,
)
from app.features.community.application.mappers.disease_community_dto_mapper import (
    DiseaseCommunityDTOMapper,
)
from app.features.community.domain.exceptions import CommunityNotFoundError


class ToggleMembershipCommandHandler:
    def __init__(self, repo: CommunityRepositoryProtocol):
        self._repo = repo

    async def handle(self, command: ToggleMembershipCommand) -> CommunityView:
        community = await self._repo.get_community(command.community_id)
        if community is None:
            raise CommunityNotFoundError()
        await self._repo.toggle_membership(community.id, command.actor.id)
        counts = await self._repo.member_counts()
        joined = community.id in await self._repo.joined_ids(command.actor.id)
        return CommunityView(
            DiseaseCommunityDTOMapper.to_output_dto(community),
            counts.get(community.id, 0),
            joined,
        )
