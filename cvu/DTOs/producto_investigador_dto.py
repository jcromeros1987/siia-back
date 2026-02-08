from dataclasses import dataclass
from uuid import UUID


@dataclass
class ProductoInvestigadorCheckerDTO:
    id: UUID
    tipo: str
    investigador: UUID
