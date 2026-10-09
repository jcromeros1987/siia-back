# ============================================================
# IMPORTACIONES
# ============================================================

# json se utiliza para leer el contenido del archivo CVU
# enviado por el usuario.
#
# El archivo CVU se recibe normalmente como un JSON.
import copy
import json


# os.path permite trabajar con rutas de archivos y directorios.
#
# En este servicio se utiliza para crear y guardar los archivos
# con las especificaciones de los formularios y de visualización.
import os.path


# asdict convierte objetos dataclass en diccionarios.
#
# Esto es necesario cuando posteriormente queremos regresar
# información de un DTO como JSON mediante Django REST Framework.
from dataclasses import asdict


# Tuple:
#   Se utiliza para indicar funciones que regresan dos valores.
#
# Any:
#   Se utiliza cuando el tipo del objeto puede variar.
from typing import Tuple, Any


# UUID representa los identificadores únicos utilizados para
# identificar usuarios e investigadores.
from uuid import UUID


# settings permite acceder a las configuraciones definidas
# en Django.
#
# En este archivo se utiliza, entre otras cosas, para obtener:
#
# settings.FORMS_ROOT
#
# que representa el directorio donde se almacenan las
# especificaciones de formularios.
from django.conf import settings


# cache es el sistema de caché de Django.
#
# Se utiliza para guardar temporalmente las especificaciones
# de formularios y de visualización y evitar generarlas
# continuamente.
from django.core.cache import cache


# ============================================================
# DTOs
# ============================================================

# ProductoInvestigadorCheckerDTO:
#
# DTO utilizado para representar información resumida o
# validada de un producto de investigador.
#
# PerfilUsuarioDTO:
#
# DTO utilizado para representar la información del perfil
# del investigador.
from cvu.DTOs import (
    ProductoInvestigadorCheckerDTO,
    PerfilUsuarioDTO,
)


# Logger utilizado para registrar información de las
# operaciones realizadas por el servicio.
from cvu.logger import logger


# Modelo ProductoInvestigador.
#
# Se utiliza directamente en get_form_data() para obtener
# un producto existente y utilizar su estructura como base
# para generar el formulario dinámico.
from cvu.models import PerfilUsuario, ProductoInvestigador


# Repositorio del CVU.
#
# CVUService delega en CVURepository las operaciones de
# acceso y modificación de datos en la base de datos.
from cvu.repository import CVURepository


# Serializer utilizado para interpretar/normalizar el
# contenido completo del CVU.
from cvu.serializers import PerfilCompletoSerializer


# Result:
#
# Clase utilizada para manejar resultados exitosos y errores
# sin depender exclusivamente de excepciones.
#
# ErrorCode:
#
# Contiene los diferentes códigos de error utilizados
# por la aplicación.
from cvu.utils import Result, ErrorCode


# ============================================================
# SERVICIO PRINCIPAL DEL CVU
# ============================================================

# Ubicación de cada tipo de producto dentro del JSON de Rizoma.
# Coincide con PerfilCompletoSerializer.
APORTACIONES_KEYS = (
    "articulosCientifica",
    "librosCientifica",
    "capitulosCientifica",
    "articulosDifusion",
    "librosDifusion",
    "capitulosDifusion",
    "desarrolloTecnologicoInnovacion",
    "propiedadIntelectual",
    "transferenciaTecnologica",
    "proyectosInvestigacion",
)

PERFIL_LIST_KEYS = (
    "trayectoriaAcademica",
    "logros",
    "trayectoriaProfesional",
    "evaluacionesOtorgadas",
    "estancias",
    "cursosImpartidos",
    "congresos",
)

FORMACION_CONTINUA_KEYS = (
    "cursos",
    "certificacionesMedicas",
)

IDIOMA_LENGUA_KEYS = (
    "idiomas",
    "lenguas",
)


def producto_para_rizoma(contenido, id_producto, fallback_id=None):
    """Devuelve el objeto de producto tal como lo espera Rizoma.

    Si el contenido no trae id, se usa id_producto. Si ese también
    falta, se usa fallback_id (el id del registro) para que el JSON
    descargado se pueda volver a cargar.
    """

    item = dict(contenido) if isinstance(contenido, dict) else {}

    if item.get("id") in (None, ""):
        identificador = id_producto or fallback_id

        if identificador:
            item["id"] = str(identificador)

    return item


def _remove_key(node, key):
    """Quita una clave de un diccionario y de los diccionarios anidados."""

    if not isinstance(node, dict):
        return

    node.pop(key, None)

    for value in node.values():
        if isinstance(value, dict):
            _remove_key(value, key)


def _place_list(document, parents, key, items):
    """Coloca una lista de productos en su ruta dentro del CVU."""

    _remove_key(document, key)

    node = document

    for parent in parents:
        current = node.get(parent)

        if not isinstance(current, dict):
            current = {}
            node[parent] = current

        node = current

    node[key] = items


def build_rizoma_cvu(perfil, productos_por_tipo, origen=None):
    """
    Arma el JSON de Rizoma.

    Si existe el archivo original, se conserva y se reescriben
    el perfil y los productos con la información actual.
    """

    document = (
        copy.deepcopy(origen)
        if isinstance(origen, dict)
        else {}
    )

    if not isinstance(document.get("perfil"), dict):
        document["perfil"] = {}

    if not isinstance(document.get("aportaciones"), dict):
        document["aportaciones"] = {}

    perfil_node = document["perfil"]

    perfil_node["cvu"] = perfil.get("cvu")
    perfil_node["nivelAcademico"] = perfil.get("nivel_academico")
    perfil_node["titulo"] = perfil.get("titulo")
    perfil_node["correoAlternativo"] = perfil.get("correo_alternativo")

    principal = perfil_node.get("principal")

    if not isinstance(principal, dict):
        principal = {}

    perfil_node["principal"] = principal

    principal.update({
        "nombre": perfil.get("nombre"),
        "primerApellido": perfil.get("primer_apellido"),
        "segundoApellido": perfil.get("segundo_apellido"),
        "fotografia": perfil.get("fotografia"),
        "semblanza": perfil.get("semblanza"),
        "linkedin": perfil.get("linkedin"),
        "orcId": perfil.get("orcid"),
        "intereses": perfil.get("intereses") or [],
        "habilidades": perfil.get("habilidades") or [],
        "curp": perfil.get("curp"),
        "rfc": perfil.get("rfc"),
        "fechaNacimiento": perfil.get("fecha_nacimiento"),
        "sexo": perfil.get("sexo"),
        "paisNacimiento": perfil.get("pais_nacimiento"),
        "entidadFederativa": perfil.get("entidad_federativa"),
        "estadoCivil": perfil.get("estado_civil"),
        "nacionalidad": perfil.get("nacionalidad"),
        "areaConocimiento": perfil.get("area_conocimiento"),
    })

    listas = {
        ("aportaciones",): APORTACIONES_KEYS,
        ("perfil",): PERFIL_LIST_KEYS,
        ("perfil", "formacionContinua"): FORMACION_CONTINUA_KEYS,
        ("perfil", "idiomaLengua"): IDIOMA_LENGUA_KEYS,
    }

    known_keys = set()

    for parents, keys in listas.items():
        for key in keys:
            known_keys.add(key)
            _place_list(
                document,
                parents,
                key,
                productos_por_tipo.get(key, []),
            )

    for tipo, items in productos_por_tipo.items():
        if tipo in known_keys:
            continue

        if tipo in document or _key_exists(document, tipo):
            _place_existing(document, tipo, items)
        else:
            document["aportaciones"][tipo] = items

    return document


def _key_exists(node, key):
    if not isinstance(node, dict):
        return False

    if key in node:
        return True

    return any(
        _key_exists(value, key)
        for value in node.values()
        if isinstance(value, dict)
    )


def _place_existing(node, key, items):
    if not isinstance(node, dict):
        return False

    if key in node:
        node[key] = items
        return True

    for value in node.values():
        if isinstance(value, dict) and _place_existing(value, key, items):
            return True

    return False


class CVUService:
    """
    Servicio encargado de implementar la lógica de negocio
    relacionada con el CVU.

    Esta clase funciona como una capa intermedia entre:

        CVUView
            |
            v
        CVUService
            |
            v
        CVURepository
            |
            v
        Base de datos

    La idea principal es que el ViewSet se encargue de recibir
    las peticiones HTTP, mientras que esta clase concentra la
    lógica necesaria para procesar los datos del CVU.
    """

    # ========================================================
    # CONSTRUCTOR
    # ========================================================

    def __init__(self):
        """
        Inicializa el servicio CVU.

        Se crea:

        1. Una instancia del repositorio.
        2. Una variable para almacenar temporalmente el catálogo
           de productos.

        _catalogo_productos comienza como None porque el catálogo
        se obtiene solamente cuando sea necesario.
        """

        # Repositorio encargado de interactuar con los modelos
        # y la base de datos.
        self.cvu_repository = CVURepository()


        # Caché interna del catálogo de productos.
        #
        # Inicialmente no se ha cargado.
        self._catalogo_productos = None


    # ========================================================
    # CATÁLOGO DE PRODUCTOS
    # ========================================================

    @property
    def catalogo_productos(self):
        """
        Obtiene el catálogo de tipos de productos CVU.

        Este método utiliza un patrón de carga diferida
        (lazy loading).

        Eso significa que el catálogo solamente se consulta
        la primera vez que alguna operación lo necesita.

        Después se conserva en:

            self._catalogo_productos
        """

        # ----------------------------------------------------
        # VERIFICAR SI YA TENEMOS EL CATÁLOGO
        # ----------------------------------------------------

        if self._catalogo_productos is None:

            # Si todavía no existe, lo solicitamos al repositorio.
            self._catalogo_productos = (
                self.cvu_repository.get_catalogo_productos()
            )


        # ----------------------------------------------------
        # DEVOLVER CATÁLOGO
        # ----------------------------------------------------

        return self._catalogo_productos


    # ========================================================
    # CREAR NUEVA ENTRADA
    # ========================================================

    def create_new_entry(
        self,
        data: dict,
        tipo: str,
        investigador_id: UUID
    ) -> Result[dict]:
        """
        Crea un nuevo producto para un investigador.

        Este método es utilizado cuando el usuario agrega
        manualmente un producto desde el formulario dinámico.

        Parámetros:

            data:
                Información del producto.

            tipo:
                Nombre del tipo de producto.

                Ejemplo:

                    articulosCientifica

            investigador_id:
                UUID del investigador que está creando el registro.

        El método:

            1. Busca el tipo de producto en el catálogo.
            2. Si existe, llama al repositorio.
            3. El repositorio realiza la validación y guardado.
        """

        # ----------------------------------------------------
        # BUSCAR TIPO DE PRODUCTO
        # ----------------------------------------------------
        #
        # get_catalogo_producto() devuelve un Result.
        #
        # and_then() permite continuar únicamente si el
        # resultado anterior fue exitoso.

        return self.cvu_repository.get_catalogo_producto(
            tipo
        ).and_then(

            # ------------------------------------------------
            # CREAR PRODUCTO
            # ------------------------------------------------
            #
            # catalogo contiene el DTO del tipo de producto
            # encontrado.

            lambda catalogo:
                self.cvu_repository.create_producto_investigador(

                    # Datos completos del producto.
                    contenido=data,

                    # Nombre del tipo de producto.
                    tipo=catalogo.nombre,

                    # Usuario/investigador propietario.
                    investigador_id=investigador_id,

                    # False significa que el registro fue
                    # creado manualmente y no proviene de
                    # un archivo CVU.
                    is_from_file=False,
                )
        )


    # ========================================================
    # ACTUALIZAR ENTRADA EXISTENTE
    # ========================================================

    def update_entry(
        self,
        id_entry: UUID,
        data: dict,
        tipo: str,
        investigador_id: UUID
    ) -> Result[ProductoInvestigadorCheckerDTO]:
        """
        Actualiza un producto existente.

        Parámetros:

            id_entry:
                ID del producto que se desea modificar.

            data:
                Nuevos datos del producto.

            tipo:
                Tipo de producto.

            investigador_id:
                Investigador propietario del producto.

        Antes de actualizar se realizan varias comprobaciones:

            1. El tipo debe existir.
            2. El producto debe existir.
            3. El producto debe pertenecer al investigador.
            4. El tipo recibido debe coincidir con el tipo
               almacenado.
        """

        # ----------------------------------------------------
        # OBTENER TIPO DEL CATÁLOGO
        # ----------------------------------------------------

        return self.cvu_repository.get_catalogo_producto(
            tipo
        ).and_then(

            # ------------------------------------------------
            # BUSCAR PRODUCTO
            # ------------------------------------------------

            lambda catalogo:
                self.cvu_repository.get_producto_investigador(
                    id_entry,
                    investigador_id
                ).and_then(

                    # ------------------------------------------
                    # VALIDAR TIPO Y ACTUALIZAR
                    # ------------------------------------------

                    lambda producto: (

                        # --------------------------------------
                        # EL TIPO NO COINCIDE
                        # --------------------------------------
                        #
                        # Si el tipo almacenado en el producto
                        # no corresponde con el tipo solicitado,
                        # regresamos un error de validación.

                        Result.err_from(
                            ErrorCode.VALIDATION_ERROR,
                            (
                                f"Tipo de producto no coincide: "
                                f"{producto.tipo} != {catalogo}"
                            ),
                        )

                        if producto.tipo != catalogo.nombre

                        # --------------------------------------
                        # ACTUALIZAR PRODUCTO
                        # --------------------------------------

                        else
                            self.cvu_repository
                            .update_producto_investigador(
                                id_entry,
                                investigador_id,
                                data,

                                # Eje actualizado.
                                data.get("eje"),

                                # Título actualizado.
                                data.get("titulo"),
                            )
                    )
                )
        )


    # ========================================================
    # LEER Y PROCESAR CVU
    # ========================================================

    def read_cvu(
            self,
            cvu_file: Any,
            investigador_id: UUID,
            autenticado_id: UUID
    ) -> Result[str]:
        """
        Lee y procesa un archivo CVU completo.

        Este es uno de los métodos más importantes del servicio.

        El flujo general es:

            Archivo JSON
                 |
                 v
            json.load()
                 |
                 v
            PerfilCompletoSerializer
                 |
                 v
            Obtener productos
                 |
                 v
            Extraer perfil
                 |
                 v
            Guardar/actualizar perfil
                 |
                 v
            Desactivar productos anteriores
                 |
                 v
            Insertar productos nuevos

        Parámetros:

            cvu_file:
                Archivo JSON recibido desde el frontend.

            investigador_id:
                Usuario al que se asociará el CVU.

            autenticado_id:
                ID del usuario autenticado obtenido mediante JWT.
                Identifica quién realiza la carga. El JSON del
                CVU no tiene que incluir usuario_id.
        """

        # ----------------------------------------------------
        # VALIDAR ARCHIVO
        # ----------------------------------------------------

        if not cvu_file:

            return Result.err_from(
                ErrorCode.INVALID_INPUT,
                "No se proporcionó un archivo CVU."
            )


        # ----------------------------------------------------
        # VALIDAR INVESTIGADOR
        # ----------------------------------------------------

        if not investigador_id:

            return Result.err_from(
                ErrorCode.INVALID_INPUT,
                "No se proporcionó un ID de investigador."
            )


        # ----------------------------------------------------
        # REGISTRAR OPERACIÓN
        # ----------------------------------------------------

        logger.info(
            "Usuario %s está cargando un CVU para el investigador %s.",
            autenticado_id,
            investigador_id,
        )


        # ----------------------------------------------------
        # LEER ARCHIVO JSON
        # ----------------------------------------------------

        try:

            # json.load() convierte el contenido del archivo
            # en estructuras Python:
            #
            # dict
            # list
            # str
            # int
            # bool
            #
            # etc.
            cvu_data = json.load(cvu_file)            

        except json.JSONDecodeError as e:

            # Si el JSON está mal formado, regresamos un error
            # de entrada inválida.
            return Result.err_from(
                ErrorCode.INVALID_INPUT,
                str(e)
            )

        # ----------------------------------------------------
        # VALIDAR NÚMERO DE CVU
        # ----------------------------------------------------
        #
        # El archivo trae el número en perfil.cvu.
        #
        # Si el usuario ya tiene un CVU en
        # app_cvu.cvu_perfil_usuarios, el del archivo debe
        # coincidir. Si todavía no hay perfil, o el CVU
        # guardado está vacío, esta es la primera carga:
        # se acepta el archivo y más adelante se crea el perfil.
        #
        # La comparación ocurre antes de serializar o de
        # modificar perfil y productos.

        perfil_json = (
            cvu_data.get("perfil", {})
            if isinstance(cvu_data, dict)
            else {}
        )

        cvu_json = (
            perfil_json.get("cvu")
            if isinstance(perfil_json, dict)
            else None
        )

        cvu_json_normalizado = (
            str(cvu_json).strip()
            if cvu_json is not None
            else ""
        )

        if not cvu_json_normalizado:

            return Result.err_from(
                ErrorCode.VALIDATION_ERROR,
                "No se puede cargar el CVU porque el archivo "
                "no contiene el número de CVU."
            )

        perfil_registrado = (
            PerfilUsuario.objects
            .filter(usuario=investigador_id)
            .first()
        )

        cvu_registrado = (
            str(perfil_registrado.cvu).strip()
            if perfil_registrado is not None
            and perfil_registrado.cvu is not None
            else ""
        )

        if cvu_registrado and cvu_json_normalizado != cvu_registrado:

            logger.warning(
                "Carga de CVU rechazada: el número de CVU del archivo "
                "no corresponde al perfil registrado. "
                "investigador_id=%s, cvu_json=%s, cvu_bd=%s",
                investigador_id,
                cvu_json,
                perfil_registrado.cvu if perfil_registrado else None,
            )

            return Result.err_from(
                ErrorCode.VALIDATION_ERROR,
                "No se puede cargar el CVU porque el número de CVU "
                "del archivo no corresponde al registrado para este usuario."
            )

        # ----------------------------------------------------
        # SERIALIZAR CVU
        # ----------------------------------------------------
        #
        # PerfilCompletoSerializer recibe la estructura completa
        # del CVU y la transforma a la estructura esperada por
        # el sistema.

        serializer = PerfilCompletoSerializer(
            instance=cvu_data
        )


        # Obtenemos los datos serializados.
        serialized_data = serializer.data


        # ----------------------------------------------------
        # EXTRAER PRODUCTOS
        # ----------------------------------------------------
        #
        # Busca dentro del CVU los tipos de productos que existen
        # en el catálogo del sistema.

        productos = self._get_productos_investigador(
            serialized_data
        )


        # ----------------------------------------------------
        # EXTRAER INFORMACIÓN DEL PERFIL
        # ----------------------------------------------------
        #
        # Convierte los nombres utilizados por el JSON CVU
        # al formato utilizado por PerfilUsuario.

        perfil_data = self.normalize_perfil_data(
            self.extract_perfil_from_cvu(
                serialized_data
            )
        )


        # ----------------------------------------------------
        # GUARDAR PERFIL
        # ----------------------------------------------------
        #
        # Crea o actualiza la información personal/académica
        # del investigador. Si no queda guardado, no se
        # continúan productos ni el JSON original: ese JSON
        # se escribe sobre el perfil recién creado.

        perfil_result = self.save_perfil_usuario(
            investigador_id,
            perfil_data
        )

        if perfil_result.is_err():

            error = perfil_result.get_error()

            logger.warning(
                "No se pudo guardar el perfil durante la carga de CVU. "
                "investigador_id=%s mensaje=%s detalles=%s",
                investigador_id,
                error.message,
                error.details,
            )

            return Result.err(error)


        # ----------------------------------------------------
        # ELIMINAR PRODUCTOS ANTERIORES
        # ----------------------------------------------------
        #
        # En realidad, debido a:
        #
        #     logic=True
        #
        # la eliminación es lógica.
        #
        # Es decir:
        #
        # status=True -> status=False
        #
        # en lugar de borrar físicamente los registros.

        return self.cvu_repository.delete_productos_investigador(
            investigador_id,
            status=True,
            is_from_file=True,
            logic=True

        ).and_then(

            # ------------------------------------------------
            # INSERTAR NUEVOS PRODUCTOS
            # ------------------------------------------------

            lambda _:
                self.cvu_repository.insert_productos_investigador(
                    productos,
                    investigador_id
                )

        ).and_then(

            # ------------------------------------------------
            # CONSERVAR EL JSON ORIGINAL
            # ------------------------------------------------
            #
            # Se guarda el documento tal como llegó de Rizoma
            # para poder reconstruirlo al descargar.

            lambda message:
                self.cvu_repository.save_cvu_origen(
                    investigador_id,
                    cvu_data,
                ).map_value(lambda _: message)
        )


    # ========================================================
    # OBTENER PRODUCTOS DEL INVESTIGADOR
    # ========================================================

    def get_productos_investigador(
        self,
        investigador_id: UUID
    ) -> dict:
        """
        Obtiene todos los productos activos de un investigador.

        El resultado se organiza por tipo de producto.

        Ejemplo conceptual:

            {
                "articulosCientifica": {
                    "nombre": "...",
                    "display_spec": {...},
                    "productos": (...)
                },

                "librosCientifica": {
                    ...
                }
            }
        """

        # Diccionario final de productos.
        productos = {}


        # ----------------------------------------------------
        # OBTENER CATÁLOGO
        # ----------------------------------------------------

        products_types_dtos = (
            self.cvu_repository
            .get_catalogo_productos()
            .unwrap()
        )


        # ----------------------------------------------------
        # CREAR DICCIONARIO NOMBRE -> ETIQUETA
        # ----------------------------------------------------
        #
        # Por ejemplo:
        #
        # articulosCientifica -> Artículos científicos

        products_names_dict = {
            dto.nombre: dto.label
            for dto in products_types_dtos
        }


        # Lista solamente con los nombres internos.
        products_names = [
            dto.nombre
            for dto in products_types_dtos
        ]


        # ----------------------------------------------------
        # RECORRER TIPOS DE PRODUCTOS
        # ----------------------------------------------------

        for producto_type in products_names:

            # Obtener productos activos de ese tipo.
            productos_instances = (
                self.cvu_repository
                .get_productos_investigador(
                    investigador_id=investigador_id,
                    tipo=producto_type,
                    status=True,
                    check_dto=False,
                )
                .unwrap_or([])
            )


            # ------------------------------------------------
            # CONSTRUIR RESPUESTA DEL TIPO
            # ------------------------------------------------

            productos[producto_type] = {

                # Nombre amigable mostrado al usuario.
                "nombre":
                    products_names_dict[producto_type],

                # Especificación utilizada para visualizar
                # los productos.
                "display_spec":
                    self.get_display_data(producto_type),

                # Convertimos cada DTO en diccionario.
                "productos": tuple(
                    asdict(instance_dto)
                    for instance_dto in productos_instances
                ),
            }


        # Regresar todos los productos agrupados por tipo.
        return productos


    # ========================================================
    # OBTENER ESPECIFICACIÓN DEL FORMULARIO
    # ========================================================

    def get_form_data(
        self,
        product_type: str
    ) -> dict:
        """
        Analiza el contenido de un producto y genera la
        especificación utilizada por el formulario dinámico.

        El formulario no está escrito manualmente campo por campo.

        En lugar de eso, este método analiza la estructura JSON
        de un producto existente y determina:

            - tipo de campo
            - orden
            - si es obligatorio
            - mensaje de validación

        IMPORTANTE:

        Actualmente el método busca primero un producto existente
        del tipo solicitado.

        Si no encuentra ninguno:

            return {}

        Esto significa que un tipo de producto sin registros
        todavía no puede generar automáticamente su formulario
        mediante este método.
        """

        # ----------------------------------------------------
        # BUSCAR PRODUCTO DE MUESTRA
        # ----------------------------------------------------

        product = (
            ProductoInvestigador.objects
            .filter(tipo__nombre=product_type)
            .first()
        )


        # ----------------------------------------------------
        # SI NO EXISTE PRODUCTO
        # ----------------------------------------------------

        if not product:
            return {}


        # ----------------------------------------------------
        # OBTENER DIRECTORIO DE FORMULARIOS
        # ----------------------------------------------------

        forms_dir = settings.FORMS_ROOT


        # Si el directorio no existe, se crea.
        if not os.path.exists(forms_dir):
            os.makedirs(forms_dir)


        # ----------------------------------------------------
        # OBTENER CLAVE DE CACHÉ
        # ----------------------------------------------------

        key = self.get_key_form_spec(
            product_type
        )


        # ----------------------------------------------------
        # CONSULTAR CACHÉ
        # ----------------------------------------------------

        if key in cache:
            return cache.get(key)


        # ----------------------------------------------------
        # GENERAR FORMULARIO
        # ----------------------------------------------------
        #
        # Se analiza el contenido JSON del producto.

        form_data, order = self._get_form_data(
            product.contenido,
            {}
        )


        # ----------------------------------------------------
        # GUARDAR EN CACHÉ
        # ----------------------------------------------------

        cache.set(
            key,
            form_data,
            timeout=None
        )


        # ----------------------------------------------------
        # GUARDAR ARCHIVO JSON
        # ----------------------------------------------------

        with open(
            os.path.join(
                forms_dir,
                f"form_spec_{product_type}.json"
            ),
            "w"
        ) as f:

            json.dump(
                form_data,
                f,
                indent=4
            )


        # Regresar especificación generada.
        return form_data


    # ========================================================
    # OBTENER DATOS DE VISUALIZACIÓN
    # ========================================================

    def get_display_data(
        self,
        product_type: str
    ) -> dict:
        """
        Obtiene la configuración utilizada para mostrar
        visualmente un producto CVU.

        La información puede estar almacenada en caché.

        Si no existe la información en caché, actualmente
        devuelve un diccionario vacío.
        """

        # Primero verificamos que el tipo de producto exista.
        result = (
            self.cvu_repository
            .get_catalogo_producto(product_type)
        )


        # Si el tipo no existe, regresamos vacío.
        if result.is_err():
            return {}


        # ----------------------------------------------------
        # CLAVE DE CACHÉ
        # ----------------------------------------------------

        key = self.get_key_display_spec(
            product_type
        )


        # ----------------------------------------------------
        # CONSULTAR CACHÉ
        # ----------------------------------------------------

        if key in cache:
            return cache.get(key)


        # Actualmente, si no existe en caché,
        # no se genera aquí.
        return {}


    # ========================================================
    # OBTENER ESPECIFICACIÓN DE DISPLAY
    # ========================================================

    def get_data_display_spec(
        self,
        products_type
    ):
        """
        Obtiene datos de especificación de visualización
        desde caché.

        Actualmente utiliza get_key_form_spec(), aunque el
        nombre del método indica que se trata de display data.
        """

        # Obtener clave.
        key = self.get_key_form_spec(
            products_type
        )


        # Si existe en caché, devolverla.
        if key in cache:
            return cache.get(key)


        # Si no existe, devolver vacío.
        return {}


    # ========================================================
    # GENERAR CLAVE PARA FORMULARIO
    # ========================================================

    def get_key_form_spec(
        self,
        product_type
    ):
        """
        Genera la clave utilizada para almacenar la
        especificación de formulario en caché.

        Ejemplo:

            product_type:
                articulosCientifica

        Resultado:

            form_spec_articulosCientifica
        """

        return f"form_spec_{product_type}"


    # ========================================================
    # GENERAR CLAVE PARA DISPLAY
    # ========================================================

    def get_key_display_spec(
        self,
        product_type
    ):
        """
        Genera la clave utilizada para la especificación
        de visualización.

        Ejemplo:

            display_spec_articulosCientifica
        """

        return f"display_spec_{product_type}"


    # ========================================================
    # GENERAR ESPECIFICACIONES DE VISUALIZACIÓN
    # ========================================================

    def gen_display_data(self):
        """
        Genera automáticamente las especificaciones necesarias
        para visualizar los diferentes tipos de productos.

        Para cada tipo de producto:

            1. Obtiene el catálogo.
            2. Busca un producto de muestra.
            3. Analiza su contenido.
            4. Genera la estructura de display.
            5. La guarda en caché.
            6. La guarda como archivo JSON.

        Los archivos resultantes se almacenan en FORMS_ROOT.
        """

        # ----------------------------------------------------
        # RECORRER CATÁLOGO
        # ----------------------------------------------------

        for tipo in (
            self.cvu_repository
            .get_catalogo_productos()
            .unwrap()
        ):

            # Crear clave de caché.
            key = self.get_key_display_spec(
                tipo.nombre
            )


            # ------------------------------------------------
            # CÓDIGO DESHABILITADO
            # ------------------------------------------------
            #
            # Estas líneas están comentadas en el código
            # original.
            #
            # Su intención aparentemente era evitar regenerar
            # información si ya existía en caché.

            # if key in cache:
            #     continue


            # ------------------------------------------------
            # OBTENER PRODUCTO DE MUESTRA
            # ------------------------------------------------

            muestra = (
                self.cvu_repository
                .get_muestra_producto_investigador(
                    tipo.nombre
                )
            )


            # ------------------------------------------------
            # SI NO EXISTE MUESTRA
            # ------------------------------------------------

            if muestra.is_err():
                continue


            # ------------------------------------------------
            # GENERAR DISPLAY DATA
            # ------------------------------------------------

            display_data, order = self._get_display_data(
                muestra.unwrap().contenido,
                {}
            )


            # ------------------------------------------------
            # GUARDAR EN CACHÉ
            # ------------------------------------------------

            cache.set(
                key,
                display_data,
                timeout=None
            )


            # ------------------------------------------------
            # GUARDAR ARCHIVO
            # ------------------------------------------------

            with open(
                os.path.join(
                    settings.FORMS_ROOT,
                    f"{key}.json"
                ),
                "w"
            ) as f:

                json.dump(
                    display_data,
                    f,
                    indent=4
                )


    # ========================================================
    # GENERAR DISPLAY DATA RECURSIVAMENTE
    # ========================================================

    def _get_display_data(
        self,
        content: dict,
        display_data: dict,
        order: int = 1
    ) -> Tuple[dict, int]:
        """
        Recorre recursivamente el contenido de un producto
        para generar la estructura utilizada para visualizarlo.

        Reconoce:

            - strings
            - enteros
            - booleanos
            - diccionarios
            - listas de diccionarios

        También genera un número de orden para cada campo.
        """

        # El orden actual comienza con el valor recibido.
        current_order = order


        # ----------------------------------------------------
        # RECORRER CONTENIDO
        # ----------------------------------------------------

        for key, value in content.items():

            # ------------------------------------------------
            # ANALIZAR TIPO DE VALOR
            # ------------------------------------------------

            match value:

                # --------------------------------------------
                # STRING / INT / BOOL
                # --------------------------------------------

                case str() | int() | bool():

                    # Para valores simples solamente se
                    # necesita label y order.
                    display_data[key] = {
                        "label": key,
                        "order": current_order
                    }


                    # Incrementar orden.
                    current_order += 1


                # --------------------------------------------
                # DICCIONARIO
                # --------------------------------------------

                case dict():

                    # Procesar recursivamente el diccionario.
                    temp_display, _ = self._get_display_data(
                        value,
                        {}
                    )


                    # Agregar etiqueta al objeto.
                    temp_display["label"] = key


                    # Asignar orden.
                    temp_display["order"] = current_order


                    # Guardar estructura.
                    display_data[key] = temp_display


                    # Incrementar orden.
                    current_order += 1


                # --------------------------------------------
                # LISTA
                # --------------------------------------------

                case list():

                    # Solamente se procesan listas cuyo primer
                    # elemento sea un diccionario.
                    if (
                        len(value) > 0
                        and isinstance(value[0], dict)
                    ):

                        # Utilizar el primer elemento como
                        # estructura de referencia.
                        temp_display, _ = (
                            self._get_display_data(
                                value[0],
                                {}
                            )
                        )


                        # Etiqueta de la lista.
                        temp_display["label"] = key


                        # Orden de la lista.
                        temp_display["order"] = current_order


                        # Indicar que se trata de una lista.
                        temp_display["list"] = True


                        # Incrementar orden.
                        current_order += 1


                        # Guardar la estructura.
                        display_data[key] = temp_display


        # ----------------------------------------------------
        # REGRESAR RESULTADO
        # ----------------------------------------------------

        return display_data, current_order


    # ========================================================
    # GENERAR ESPECIFICACIÓN DE FORMULARIO
    # ========================================================

    def _get_form_data(
        self,
        content_json: dict,
        form_data: dict,
        order: int = 1
    ) -> Tuple[dict, int]:
        """
        Recorre recursivamente un JSON de producto para
        construir la especificación del formulario.

        Cada tipo de dato se convierte en un tipo de campo:

            str
                -> text

            bool
                -> checkbox

            int
                -> number

            dict
                -> objeto anidado

            list
                -> lista de objetos

        Los campos:

            eje
            titulo

        se consideran obligatorios.
        """

        # Orden actual.
        current_order = order


        # ----------------------------------------------------
        # CAMPOS OBLIGATORIOS
        # ----------------------------------------------------
        #
        # Estos dos campos se consideran requeridos por el
        # generador automático del formulario.

        required_fields = [
            "eje",
            "titulo"
        ]


        # ----------------------------------------------------
        # RECORRER JSON
        # ----------------------------------------------------

        for key, value in content_json.items():

            # ------------------------------------------------
            # IGNORAR ID
            # ------------------------------------------------
            #
            # El ID no se captura mediante el formulario.
            if key == "id":
                continue


            # ------------------------------------------------
            # DETERMINAR TIPO
            # ------------------------------------------------

            match value:

                # --------------------------------------------
                # TEXTO
                # --------------------------------------------

                case str():

                    form_data[key] = {
                        "type": "text",
                        "final": True,
                        "order": current_order,

                        # El campo es obligatorio únicamente
                        # si su nombre está en required_fields.
                        "required":
                            key in required_fields,

                        # Mensaje mostrado si el campo requerido
                        # no tiene información.
                        "invalid_feedback":
                            "Este campo es requerido"
                            if key in required_fields
                            else "",
                    }


                    # Incrementar orden.
                    current_order += 1


                # --------------------------------------------
                # BOOLEANO
                # --------------------------------------------

                case bool():

                    form_data[key] = {
                        "type": "checkbox",
                        "final": True,
                        "order": current_order,
                        "required":
                            key in required_fields,
                        "invalid_feedback":
                            "Este campo es requerido"
                            if key in required_fields
                            else "",
                    }


                    # Incrementar orden.
                    current_order += 1


                # --------------------------------------------
                # ENTERO
                # --------------------------------------------

                case int():

                    form_data[key] = {
                        "type": "number",
                        "final": True,
                        "order": current_order,
                        "required":
                            key in required_fields,

                        # Mensaje diferente dependiendo de si
                        # es obligatorio.
                        "invalid_feedback":
                            "Este campo es requerido"
                            if key in required_fields
                            else
                            "El valor debe ser un número entero",
                    }


                    # Incrementar orden.
                    current_order += 1


                # --------------------------------------------
                # OBJETO
                # --------------------------------------------

                case dict():

                    # Procesar recursivamente el objeto.
                    temp_form, current_order = (
                        self._get_form_data(
                            value,
                            {},
                            current_order
                        )
                    )


                    # Guardar el formulario generado para
                    # ese objeto.
                    form_data[key] = temp_form


                # --------------------------------------------
                # LISTA
                # --------------------------------------------

                case list():

                    # El código original utiliza el primer
                    # elemento de la lista como estructura
                    # de referencia.
                    temp_form, current_order = (
                        self._get_form_data(
                            value[0],
                            {},
                            current_order
                        )
                    )


                    # Marcar la estructura como lista.
                    temp_form["list"] = True


                    # Guardar estructura.
                    form_data[key] = temp_form


        # ----------------------------------------------------
        # REGRESAR RESULTADO
        # ----------------------------------------------------

        return form_data, current_order


    # ========================================================
    # OBTENER PRODUCTOS DESDE EL CVU
    # ========================================================

    def _get_productos_investigador(
        self,
        cvu_data: dict
    ) -> dict:
        """
        Busca dentro del CVU todos los tipos de productos
        que estén registrados en el catálogo del sistema.

        El CVU puede contener una estructura bastante profunda.

        Por eso posteriormente se utiliza:

            _get_productos_investigador_aux()

        para recorrerla recursivamente.
        """

        # Diccionario donde se almacenarán los productos
        # encontrados.
        productos = {}


        # ----------------------------------------------------
        # OBTENER TIPOS DEL CATÁLOGO
        # ----------------------------------------------------

        tipos = (
            self.catalogo_productos
            .map_value(
                lambda tipos_cat:
                    [
                        tipo.nombre
                        for tipo in tipos_cat
                    ]
            )
            .unwrap()
        )


        # ----------------------------------------------------
        # BUSCAR RECURSIVAMENTE
        # ----------------------------------------------------

        self._get_productos_investigador_aux(
            cvu_data,
            tipos,
            productos
        )


        # Regresar productos encontrados.
        return productos


    # ========================================================
    # MÉTODO AUXILIAR PARA BUSCAR PRODUCTOS
    # ========================================================

    def _get_productos_investigador_aux(
        self,
        cvu_data: dict,
        tipos: list,
        productos: dict
    ):
        """
        Recorre recursivamente el CVU buscando claves que
        coincidan con los tipos registrados en el catálogo.

        Ejemplo conceptual:

            CVU
             |
             +-- perfil
             |
             +-- aportaciones
                    |
                    +-- articulosCientifica
                    |
                    +-- librosCientifica

        Si encuentra una clave que coincide con un tipo
        registrado en "tipos", la agrega a "productos".
        """

        # ----------------------------------------------------
        # RECORRER DICCIONARIO
        # ----------------------------------------------------

        for key, value in cvu_data.items():

            # ------------------------------------------------
            # ¿ES UN TIPO DE PRODUCTO?
            # ------------------------------------------------

            if key in tipos:

                # Guardamos directamente la información.
                productos[key] = value


            # ------------------------------------------------
            # ¿ES OTRO DICCIONARIO?
            # ------------------------------------------------
            #
            # Si no es un tipo de producto pero el valor es
            # un diccionario, seguimos buscando dentro de él.

            elif isinstance(value, dict):

                self._get_productos_investigador_aux(
                    value,
                    tipos,
                    productos
                )


    # ========================================================
    # MÉTODOS PARA PERFILUSUARIO
    # ========================================================

    # Este bloque contiene operaciones relacionadas con la
    # información de perfil del investigador.


    # ========================================================
    # GUARDAR PERFIL
    # ========================================================

    def save_perfil_usuario(
        self,
        investigador_id: UUID,
        data: dict
    ) -> Result[PerfilUsuarioDTO]:
        """
        Crea o actualiza el perfil del investigador.

        El acceso real a la base de datos se delega al
        CVURepository.
        """

        # Registrar operación en log.
        logger.info(
            f"Saving profile for investigador_id: "
            f"{investigador_id}"
        )


        # Delegar la operación al repositorio.
        return self.cvu_repository.create_or_update_perfil_usuario(
            investigador_id,
            data
        )


    # ========================================================
    # OBTENER PERFIL
    # ========================================================

    def export_cvu(
        self,
        investigador_id: UUID
    ) -> Result[dict]:
        """
        Arma el JSON de Rizoma con el perfil y los productos actuales.

        Si el investigador ya cargó un archivo, la descarga parte
        de ese documento y conserva los campos que esta aplicación
        no modifica.
        """

        perfil_result = self.get_perfil_usuario(investigador_id)

        if perfil_result.is_err():
            return Result.err(perfil_result.get_error())

        perfil = asdict(perfil_result.unwrap())

        productos = (
            ProductoInvestigador.objects
            .filter(
                investigador_id=investigador_id,
                status=True,
            )
            .select_related("tipo")
            .order_by("fecha_creacion", "id")
        )

        productos_por_tipo = {}

        for producto in productos:
            item = producto_para_rizoma(
                producto.contenido,
                producto.id_producto,
                producto.id,
            )

            productos_por_tipo.setdefault(
                producto.tipo.nombre,
                [],
            ).append(item)

        perfil_model = (
            PerfilUsuario.objects
            .filter(usuario=investigador_id)
            .first()
        )

        origen = (
            perfil_model.cvu_origen
            if perfil_model is not None
            and isinstance(perfil_model.cvu_origen, dict)
            else None
        )

        return Result.ok(
            build_rizoma_cvu(
                perfil,
                productos_por_tipo,
                origen,
            )
        )


    def get_perfil_usuario(
        self,
        investigador_id: UUID
    ) -> Result[PerfilUsuarioDTO]:
        """
        Obtiene el perfil de un investigador.

        El servicio delega la consulta al repositorio.
        """

        # Registrar operación.
        logger.info(
            f"Retrieving profile for investigador_id: "
            f"{investigador_id}"
        )


        # Consultar repositorio.
        return self.cvu_repository.get_perfil_usuario(
            investigador_id
        )


    # ========================================================
    # ELIMINAR PERFIL
    # ========================================================

    def delete_perfil_usuario(
        self,
        investigador_id: UUID
    ) -> Result[str]:
        """
        Elimina el perfil de un investigador.

        Esta operación también es delegada al repositorio.
        """

        # Registrar operación.
        logger.info(
            f"Deleting profile for investigador_id: "
            f"{investigador_id}"
        )


        # Ejecutar eliminación.
        return self.cvu_repository.delete_perfil_usuario(
            investigador_id
        )


    # ========================================================
    # EXTRAER PERFIL DESDE EL CVU
    # ========================================================

    def normalize_perfil_data(self, data: dict) -> dict:
        """
        Ajusta el perfil extraído del JSON para que pueda crearse
        aunque Rizoma mande textos vacíos o tipos distintos a los
        del modelo.
        """

        normalized = dict(data)
        text_limits = {
            "cvu": 128,
            "nivel_academico": 255,
            "titulo": 512,
            "nombre": 255,
            "primer_apellido": 255,
            "segundo_apellido": 255,
            "linkedin": 512,
            "orcid": 64,
            "curp": 18,
            "rfc": 13,
        }

        for key in (
            "cvu",
            "nivel_academico",
            "titulo",
            "nombre",
            "primer_apellido",
            "segundo_apellido",
            "semblanza",
            "linkedin",
            "orcid",
            "correo_alternativo",
            "curp",
            "rfc",
            "fecha_nacimiento",
        ):
            value = normalized.get(key)

            if isinstance(value, str):
                value = value.strip() or None

            if isinstance(value, str) and key in text_limits:
                value = value[: text_limits[key]]

            normalized[key] = value

        fecha = normalized.get("fecha_nacimiento")

        if isinstance(fecha, str):
            fecha = fecha[:10]
            normalized["fecha_nacimiento"] = (
                fecha
                if len(fecha) == 10 and fecha[4] == "-" and fecha[7] == "-"
                else None
            )

        linkedin = normalized.get("linkedin")

        if isinstance(linkedin, str) and not linkedin.startswith(
            ("http://", "https://")
        ):
            normalized["linkedin"] = None

        correo = normalized.get("correo_alternativo")

        if isinstance(correo, str) and "@" not in correo:
            normalized["correo_alternativo"] = None

        fotografia = normalized.get("fotografia")

        if isinstance(fotografia, str):
            fotografia = fotografia.strip()
            normalized["fotografia"] = (
                {
                    "nombre": None,
                    "contentType": None,
                    "uri": fotografia,
                }
                if fotografia
                else None
            )
        elif fotografia is not None and not isinstance(fotografia, dict):
            normalized["fotografia"] = None

        for key in (
            "sexo",
            "pais_nacimiento",
            "entidad_federativa",
            "estado_civil",
            "nacionalidad",
            "area_conocimiento",
        ):
            value = normalized.get(key)

            if value is not None and not isinstance(value, dict):
                normalized[key] = None

        for key in ("intereses", "habilidades"):
            if not isinstance(normalized.get(key), list):
                normalized[key] = []

        return normalized

    def extract_perfil_from_cvu(
        self,
        cvu_data: dict
    ) -> dict:
        """
        Extrae la información de perfil desde el JSON completo
        del CVU.

        El JSON original utiliza nombres como:

            nivelAcademico
            primerApellido
            segundoApellido
            fechaNacimiento
            orcId

        mientras que el modelo interno utiliza nombres como:

            nivel_academico
            primer_apellido
            segundo_apellido
            fecha_nacimiento
            orcid

        Este método realiza esa transformación.
        """

        # ----------------------------------------------------
        # OBTENER OBJETO PERFIL
        # ----------------------------------------------------

        perfil_data = cvu_data.get(
            "perfil",
            {}
        )


        # ----------------------------------------------------
        # OBTENER OBJETO PRINCIPAL
        # ----------------------------------------------------

        principal_data = perfil_data.get(
            "principal",
            {}
        )


        # ----------------------------------------------------
        # CONSTRUIR DICCIONARIO INTERNO
        # ----------------------------------------------------

        return {

            # Número CVU.
            "cvu":
                perfil_data.get("cvu"),


            # Nivel académico.
            "nivel_academico":
                perfil_data.get("nivelAcademico"),


            # Título académico.
            "titulo":
                perfil_data.get("titulo"),


            # Nombre.
            "nombre":
                principal_data.get("nombre"),


            # Primer apellido.
            "primer_apellido":
                principal_data.get("primerApellido"),


            # Segundo apellido.
            "segundo_apellido":
                principal_data.get("segundoApellido"),


            # Fotografía.
            "fotografia":
                principal_data.get("fotografia"),


            # Semblanza.
            "semblanza":
                principal_data.get("semblanza"),

            # LinkedIn.
            "linkedin":
                principal_data.get("linkedin"),

            # Correo alternativo.
            "correo_alternativo":
            perfil_data.get("correoAlternativo"),

            # ORCID.
            #
            # El JSON utiliza "orcId".
            # El sistema interno utiliza "orcid".
            "orcid":
                principal_data.get("orcId"),


            # Intereses del investigador.
            "intereses":
                principal_data.get(
                    "intereses",
                    []
                ),


            # Habilidades.
            "habilidades":
                principal_data.get(
                    "habilidades",
                    []
                ),


            # CURP.
            "curp":
                principal_data.get("curp"),


            # RFC.
            "rfc":
                principal_data.get("rfc"),


            # Fecha de nacimiento.
            "fecha_nacimiento":
                principal_data.get("fechaNacimiento"),


            # Sexo.
            "sexo":
                principal_data.get("sexo"),


            # País de nacimiento.
            "pais_nacimiento":
                principal_data.get("paisNacimiento"),


            # Entidad federativa.
            "entidad_federativa":
                principal_data.get("entidadFederativa"),


            # Estado civil.
            "estado_civil":
                principal_data.get("estadoCivil"),


            # Nacionalidad.
            "nacionalidad":
                principal_data.get("nacionalidad"),


            # Área de conocimiento.
            "area_conocimiento":
                principal_data.get("areaConocimiento"),
        }