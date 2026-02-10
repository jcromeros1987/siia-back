from dataclasses import dataclass
from uuid import UUID


@dataclass
class ProductoInvestigadorCheckerDTO:
    id: UUID
    tipo: str
    investigador: UUID


@dataclass
class ProductoInvestigadorDTO:
    id: UUID
    tipo: str
    investigador: UUID
    contenido: dict
    eje: str
    titulo: str
    status: bool
    is_from_file: bool
