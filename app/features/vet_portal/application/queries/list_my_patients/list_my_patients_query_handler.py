from app.features.vet_portal.application.dtos.vet_patient import VetPatient
from app.features.vet_portal.application.queries.list_my_patients.list_my_patients_query import (
    ListMyPatientsQuery,
)
from app.features.vet_portal.application.services.vet_caseload import VetCaseload


class ListMyPatientsQueryHandler:
    def __init__(self, caseload: VetCaseload):
        self._caseload = caseload

    async def handle(self, query: ListMyPatientsQuery) -> list[VetPatient]:
        return await self._caseload.patients_of(query.actor)
