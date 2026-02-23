from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from uuid import UUID


@dataclass
class PerfilUsuarioDTO:
    """DTO para lectura completa del perfil de usuario."""

    id: UUID
    usuario_id: UUID
    cvu: Optional[str]
    nivel_academico: Optional[str]
    titulo: Optional[str]
    nombre: Optional[str]
    primer_apellido: Optional[str]
    segundo_apellido: Optional[str]
    fotografia: Optional[Dict[str, Optional[str]]]
    semblanza: Optional[str]
    linkedin: Optional[str]
    orcid: Optional[str]
    correo_alternativo: Optional[str]
    curp: Optional[str]
    rfc: Optional[str]
    fecha_nacimiento: Optional[str]
    intereses: List[str] = field(default_factory=list)
    habilidades: List[str] = field(default_factory=list)
    sexo: Optional[Dict[str, Any]] = None
    pais_nacimiento: Optional[Dict[str, Any]] = None
    entidad_federativa: Optional[Dict[str, Any]] = None
    estado_civil: Optional[Dict[str, Any]] = None
    nacionalidad: Optional[Dict[str, Any]] = None
    area_conocimiento: Optional[Dict[str, Any]] = None
    fecha_creacion: Optional[str] = None
    fecha_modificacion: Optional[str] = None


@dataclass
class PerfilUsuarioCheckDTO:
    """DTO minimal para verificación de existencia del perfil."""

    id: UUID
    usuario_id: UUID
    cvu: Optional[str]
