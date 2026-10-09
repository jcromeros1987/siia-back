# Importa el módulo uuid de Python.
# Se utiliza para generar identificadores UUID automáticamente
# para los registros del perfil.
import uuid


# Importa el módulo de modelos de Django.
# Con esto podemos definir la tabla y sus columnas mediante ORM.
from django.db import models


# Importa el modelo User utilizado por el sistema CVU.
# PerfilUsuario tendrá una relación directa con este usuario.
from cvu.models import User


# Define el modelo PerfilUsuario.
#
# Este modelo representa la información personal y académica
# asociada a un usuario del sistema.
class PerfilUsuario(models.Model):

    """
    Modelo para almacenar la información personal del usuario
    que no es Producto de Investigación.

    Incluye datos del perfil e información principal
    del investigador.
    """

    # ---------------------------------------------------------
    # IDENTIFICADOR DEL PERFIL
    # ---------------------------------------------------------

    # Campo UUID que funciona como llave primaria de la tabla.
    #
    # primary_key=True:
    #   Este campo identifica de manera única al registro.
    #
    # default=uuid.uuid4:
    #   Si no se proporciona un UUID, Django genera uno automáticamente.
    #
    # editable=False:
    #   No se permite editar este valor desde formularios administrativos.
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )


    # Relación uno a uno entre PerfilUsuario y User.
    #
    # Esto significa que un usuario solamente puede tener
    # un perfil asociado.
    usuario = models.OneToOneField(

        # Modelo de usuario al que pertenece este perfil.
        User,

        # Si se elimina el usuario, también se elimina su perfil.
        on_delete=models.CASCADE,

        # El usuario es obligatorio.
        null=False,

        # No puede dejarse vacío en formularios.
        blank=False,

        # Permite acceder desde User mediante:
        #
        # usuario.perfil
        #
        related_name="perfil"
    )


    # ---------------------------------------------------------
    # INFORMACIÓN PRINCIPAL
    # ---------------------------------------------------------

    # Número o identificador CVU del investigador.
    #
    # Puede ser NULL y también puede dejarse vacío.
    cvu = models.CharField(
        max_length=128,
        null=True,
        blank=True
    )


    # Nivel académico máximo del investigador.
    #
    # Ejemplo:
    # "LICENCIATURA"
    # "Maestría"
    # "Doctorado"
    nivel_academico = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )


    # Título académico o prefijo/título principal.
    #
    # Ejemplo:
    # "Lic."
    # "Ingeniero en Sistemas Computacionales"
    titulo = models.CharField(
        max_length=512,
        null=True,
        blank=True
    )


    # Nombre del investigador.
    nombre = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )


    # Primer apellido.
    primer_apellido = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )


    # Segundo apellido.
    segundo_apellido = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )


    # ---------------------------------------------------------
    # INFORMACIÓN PERSONAL
    # ---------------------------------------------------------

    # Nombre original de la fotografía.
    fotografia_nombre = models.CharField(
        max_length=512,
        null=True,
        blank=True
    )


    # Tipo MIME de la fotografía.
    #
    # Ejemplo:
    # "image/jpeg"
    fotografia_content_type = models.CharField(
        max_length=128,
        null=True,
        blank=True
    )


    # Ubicación/URI de la fotografía.
    #
    # Se utiliza TextField porque una URI puede ser relativamente larga.
    fotografia_uri = models.TextField(
        null=True,
        blank=True
    )


    # Semblanza o descripción profesional del investigador.
    semblanza = models.TextField(
        null=True,
        blank=True
    )


    # ---------------------------------------------------------
    # INFORMACIÓN DE CONTACTO
    # ---------------------------------------------------------

    # URL del perfil de LinkedIn.
    #
    # URLField permite que Django valide que el contenido
    # tenga formato de URL.
    linkedin = models.URLField(
        max_length=512,
        null=True,
        blank=True
    )


    # Identificador ORCID.
    orcid = models.CharField(
        max_length=64,
        null=True,
        blank=True
    )


    # Correo electrónico alternativo.
    #
    # EmailField realiza validaciones básicas de correo.
    correo_alternativo = models.EmailField(
        null=True,
        blank=True
    )


    # ---------------------------------------------------------
    # INFORMACIÓN DEMOGRÁFICA
    # ---------------------------------------------------------

    # CURP del investigador.
    #
    # La CURP mexicana tiene 18 caracteres.
    curp = models.CharField(
        max_length=18,
        null=True,
        blank=True
    )


    # RFC del investigador.
    #
    # Se permite hasta 13 caracteres.
    rfc = models.CharField(
        max_length=13,
        null=True,
        blank=True
    )


    # Fecha de nacimiento.
    #
    # Django la almacena como fecha, no como texto.
    fecha_nacimiento = models.DateField(
        null=True,
        blank=True
    )


    # ---------------------------------------------------------
    # INFORMACIÓN ADICIONAL ALMACENADA COMO JSON
    # ---------------------------------------------------------

    # Lista de intereses.
    #
    # JSONField permite almacenar estructuras JSON.
    #
    # default=list:
    #   Si no se proporciona información, el valor predeterminado
    #   es una lista vacía.
    intereses = models.JSONField(
        default=list,
        null=True,
        blank=True
    )


    # Lista de habilidades.
    #
    # También se almacena como JSON.
    habilidades = models.JSONField(
        default=list,
        null=True,
        blank=True
    )


    # Sexo.
    #
    # IMPORTANTE:
    # Este campo NO es CharField.
    #
    # Está diseñado para almacenar algo como:
    #
    # {
    #     "id": "...",
    #     "nombre": "Masculino"
    # }
    sexo = models.JSONField(
        null=True,
        blank=True
    )


    # País de nacimiento.
    #
    # También está diseñado para almacenar un objeto JSON.
    #
    # Ejemplo:
    #
    # {
    #     "id": "MEX",
    #     "nombre": "México"
    # }
    pais_nacimiento = models.JSONField(
        null=True,
        blank=True
    )


    # Entidad federativa.
    #
    # También se almacena como JSON.
    entidad_federativa = models.JSONField(
        null=True,
        blank=True
    )


    # Estado civil.
    #
    # El comentario indica que se espera:
    #
    # {
    #     "id": "...",
    #     "nombre": "Casado"
    # }
    estado_civil = models.JSONField(
        null=True,
        blank=True
    )


    # Nacionalidad.
    #
    # También se espera un objeto JSON:
    #
    # {
    #     "id": "...",
    #     "nombre": "Mexicana"
    # }
    nacionalidad = models.JSONField(
        null=True,
        blank=True
    )


    # Área de conocimiento.
    #
    # El comentario indica una estructura aproximada:
    #
    # {
    #     "area": ...,
    #     "campo": ...,
    #     "disciplina": ...,
    #     "subdisciplina": ...
    # }
    area_conocimiento = models.JSONField(
        null=True,
        blank=True
    )


    # ---------------------------------------------------------
    # METADATOS
    # ---------------------------------------------------------

    # Fecha y hora en que se creó el perfil.
    #
    # auto_now_add=True significa que Django la establece
    # automáticamente solamente cuando se crea el registro.
    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )


    # Fecha y hora de la última modificación.
    #
    # auto_now=True significa que Django actualiza automáticamente
    # este valor cada vez que se guarda el registro.
    fecha_modificacion = models.DateTimeField(
        auto_now=True
    )


    # JSON original cargado desde Rizoma.
    #
    # La descarga parte de este documento y reescribe el perfil
    # y los productos con la información actual, para conservar
    # campos que el sistema no edita (institución, filtro, login).
    cvu_origen = models.JSONField(
        null=True,
        blank=True
    )


    # ---------------------------------------------------------
    # CONFIGURACIÓN DEL MODELO
    # ---------------------------------------------------------

    class Meta:

        # Nombre real de la tabla en PostgreSQL.
        db_table = "cvu_perfil_usuarios"


        # Nombre singular utilizado por Django Admin.
        verbose_name = "Perfil Usuario"


        # Nombre plural utilizado por Django Admin.
        verbose_name_plural = "Perfiles Usuarios"


    # ---------------------------------------------------------
    # REPRESENTACIÓN DEL OBJETO
    # ---------------------------------------------------------

    def __str__(self):

        # Cuando Django necesita representar el perfil como texto,
        # devuelve:
        #
        # Perfil de correo@ejemplo.com
        #
        return f"Perfil de {self.usuario.email}"


    # ---------------------------------------------------------
    # CONVERSIÓN DEL MODELO A DICCIONARIO
    # ---------------------------------------------------------

    def to_dict(self) -> dict:

        """
        Convierte el perfil a un diccionario.
        """

        # Devuelve toda la información del perfil
        # en forma de diccionario Python.
        return {

            # Convierte el UUID a texto para que pueda serializarse
            # fácilmente a JSON.
            "id": str(self.id),


            # Convierte también el UUID del usuario a texto.
            "usuario_id": str(self.usuario.id),


            # Información principal.
            "cvu": self.cvu,
            "nivel_academico": self.nivel_academico,
            "titulo": self.titulo,
            "nombre": self.nombre,
            "primer_apellido": self.primer_apellido,
            "segundo_apellido": self.segundo_apellido,


            # -------------------------------------------------
            # FOTOGRAFÍA
            # -------------------------------------------------

            # Si existe una URI de fotografía,
            # construye un objeto con sus datos.
            "fotografia": {

                # Nombre del archivo.
                "nombre": self.fotografia_nombre,

                # Tipo MIME.
                "contentType": self.fotografia_content_type,

                # URI de la fotografía.
                "uri": self.fotografia_uri,

            }

            # Solamente construye el objeto anterior si
            # fotografia_uri tiene algún valor.
            if self.fotografia_uri

            # Si no existe fotografía, devuelve None.
            else None,


            # Semblanza.
            "semblanza": self.semblanza,


            # LinkedIn.
            "linkedin": self.linkedin,


            # ORCID.
            #
            # Aquí el nombre que sale en el diccionario es "orcId",
            # aunque la columna del modelo se llama "orcid".
            "orcId": self.orcid,


            # Correo alternativo.
            "correo_alternativo": self.correo_alternativo,


            # CURP.
            "curp": self.curp,


            # RFC.
            "rfc": self.rfc,


            # Fecha de nacimiento.
            #
            # Si existe una fecha, se convierte a ISO:
            #
            # 1988-04-15
            #
            # Si no existe, devuelve None.
            "fecha_nacimiento": self.fecha_nacimiento.isoformat()
            if self.fecha_nacimiento
            else None,


            # Intereses.
            #
            # Si self.intereses es None, devuelve [].
            "intereses": self.intereses or [],


            # Habilidades.
            #
            # Si self.habilidades es None, devuelve [].
            "habilidades": self.habilidades or [],


            # -------------------------------------------------
            # CAMPOS JSON
            # -------------------------------------------------

            # Aquí se devuelve el JSON completo almacenado.
            #
            # NO se obtiene solamente ["nombre"].
            "sexo": self.sexo,

            "pais_nacimiento": self.pais_nacimiento,

            "entidad_federativa": self.entidad_federativa,

            "estado_civil": self.estado_civil,

            "nacionalidad": self.nacionalidad,

            "area_conocimiento": self.area_conocimiento,


            # -------------------------------------------------
            # FECHAS DEL REGISTRO
            # -------------------------------------------------

            # Fecha de creación convertida a texto ISO.
            "fecha_creacion": self.fecha_creacion.isoformat(),


            # Fecha de modificación convertida a texto ISO.
            "fecha_modificacion": self.fecha_modificacion.isoformat(),
        }