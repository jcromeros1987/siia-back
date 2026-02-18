import uuid

from django.db import models
from cvu.models import User


class PerfilUsuario(models.Model):
    """
    Modelo para almacenar la información personal del usuario que no es Producto de Investigación.
    Incluye datos del perfil e información principal del investigador.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.OneToOneField(
        User, on_delete=models.CASCADE, null=False, blank=False, related_name="perfil"
    )

    # Información Principal
    cvu = models.CharField(max_length=128, null=True, blank=True)
    nivel_academico = models.CharField(max_length=255, null=True, blank=True)
    titulo = models.CharField(max_length=512, null=True, blank=True)

    # Información Personal (fotografía y semblanza)
    fotografia_nombre = models.CharField(max_length=512, null=True, blank=True)
    fotografia_content_type = models.CharField(max_length=128, null=True, blank=True)
    fotografia_uri = models.TextField(null=True, blank=True)
    semblanza = models.TextField(null=True, blank=True)

    # Información de Contacto
    linkedin = models.URLField(max_length=512, null=True, blank=True)
    orcid = models.CharField(max_length=64, null=True, blank=True)
    correo_alternativo = models.EmailField(null=True, blank=True)

    # Información Demográfica
    curp = models.CharField(max_length=18, null=True, blank=True)
    rfc = models.CharField(max_length=13, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)

    # Información Adicional (stored as JSON)
    intereses = models.JSONField(default=list, null=True, blank=True)
    habilidades = models.JSONField(default=list, null=True, blank=True)
    sexo = models.JSONField(null=True, blank=True)  # {id, nombre}
    pais_nacimiento = models.JSONField(null=True, blank=True)  # {id, nombre}
    entidad_federativa = models.JSONField(null=True, blank=True)
    estado_civil = models.JSONField(null=True, blank=True)  # {id, nombre}
    nacionalidad = models.JSONField(null=True, blank=True)  # {id, nombre}
    area_conocimiento = models.JSONField(
        null=True, blank=True
    )  # {area, campo, disciplina, subdisciplina}

    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cvu_perfil_usuarios"
        verbose_name = "Perfil Usuario"
        verbose_name_plural = "Perfiles Usuarios"

    def __str__(self):
        return f"Perfil de {self.usuario.email}"

    def to_dict(self) -> dict:
        """Convierte el perfil a diccionario."""
        return {
            "id": str(self.id),
            "usuario_id": str(self.usuario.id),
            "cvu": self.cvu,
            "nivel_academico": self.nivel_academico,
            "titulo": self.titulo,
            "fotografia": {
                "nombre": self.fotografia_nombre,
                "contentType": self.fotografia_content_type,
                "uri": self.fotografia_uri,
            }
            if self.fotografia_uri
            else None,
            "semblanza": self.semblanza,
            "linkedin": self.linkedin,
            "orcId": self.orcid,
            "correo_alternativo": self.correo_alternativo,
            "curp": self.curp,
            "rfc": self.rfc,
            "fecha_nacimiento": self.fecha_nacimiento.isoformat()
            if self.fecha_nacimiento
            else None,
            "intereses": self.intereses or [],
            "habilidades": self.habilidades or [],
            "sexo": self.sexo,
            "pais_nacimiento": self.pais_nacimiento,
            "entidad_federativa": self.entidad_federativa,
            "estado_civil": self.estado_civil,
            "nacionalidad": self.nacionalidad,
            "area_conocimiento": self.area_conocimiento,
            "fecha_creacion": self.fecha_creacion.isoformat(),
            "fecha_modificacion": self.fecha_modificacion.isoformat(),
        }
