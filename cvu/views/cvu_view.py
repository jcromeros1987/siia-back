# ============================================================
# IMPORTACIONES
# ============================================================

# asdict permite convertir objetos tipo dataclass a diccionarios.
#
# Se utiliza posteriormente cuando necesitamos regresar
# información de un DTO dentro de una respuesta HTTP.
from dataclasses import asdict


# Importamos los códigos de estado HTTP que utiliza Django REST
# Framework para construir las respuestas.
#
# Ejemplos:
#
# status.HTTP_200_OK
# status.HTTP_201_CREATED
# status.HTTP_400_BAD_REQUEST
# status.HTTP_404_NOT_FOUND
from rest_framework import status


# "action" permite crear endpoints adicionales dentro de un
# ViewSet.
#
# Por ejemplo:
#
# /api/v1/cvu/create-entry/
# /api/v1/cvu/update-entry/
# /api/v1/cvu/form/<product_type>/
from rest_framework.decorators import action


# Permiso que obliga a que el usuario esté autenticado para
# poder acceder a los endpoints del CVU.
from rest_framework.permissions import IsAuthenticated


# Response es la respuesta HTTP que devolveremos al frontend.
from rest_framework.response import Response


# ViewSet es la clase base utilizada para crear el controlador
# del módulo CVU.
from rest_framework.viewsets import ViewSet


# Autenticación mediante JSON Web Token (JWT).
#
# El frontend envía el token mediante:
#
# Authorization: Bearer <access_token>
#
# y Django REST Framework utiliza esta clase para identificar
# al usuario autenticado.
from rest_framework_simplejwt.authentication import JWTAuthentication


# Logger utilizado para registrar acontecimientos importantes
# durante la ejecución del backend.
from cvu.logger import logger


# Servicio principal del módulo CVU.
#
# CVUView se encarga de HTTP.
# CVUService se encarga de la lógica de negocio.
from cvu.domain import CVUService


# Modelos utilizados directamente por este ViewSet.
#
# User:
#   Representa al usuario/investigador.
#
# CatalogoProducto:
#   Catálogo que contiene los diferentes tipos de productos
#   académicos del CVU.
from cvu.models import User, CatalogoProducto


# ErrorCode contiene los códigos utilizados por el objeto
# Result para identificar diferentes tipos de errores.
from cvu.utils import ErrorCode


# ============================================================
# VIEWSET DEL CVU
# ============================================================

class CVUView(ViewSet):
    """
    ViewSet para manejar operaciones relacionadas con el CVU
    (Currículum Vitae Único) de los usuarios.

    Este ViewSet funciona como la capa HTTP del módulo CVU.

    Su responsabilidad principal es:

    - Recibir peticiones del frontend.
    - Obtener parámetros de la petición.
    - Validar información básica.
    - Invocar al CVUService.
    - Convertir los resultados en respuestas HTTP.

    La lógica más importante de procesamiento de datos no está
    directamente aquí; se encuentra principalmente en:

        cvu/domain/cvu_service.py

    ============================================================
    ENDPOINTS PRINCIPALES
    ============================================================

    GET:

        /api/v1/cvu/<usuario_id>

    Obtiene la información del CVU de un usuario.

    POST:

        /api/v1/cvu/

    Recibe un archivo JSON completo del CVU.

    POST:

        /api/v1/cvu/create-entry/

    Crea manualmente un nuevo producto.

    PATCH:

        /api/v1/cvu/update-entry/

    Actualiza un producto existente.

    GET:

        /api/v1/cvu/form/<product_type>/

    Obtiene la estructura del formulario dinámico.
    """

    # ========================================================
    # AUTENTICACIÓN
    # ========================================================

    # Todas las peticiones realizadas contra este ViewSet
    # requieren un JWT válido.
    #
    # El frontend debe enviar:
    #
    # Authorization: Bearer <access_token>
    #
    authentication_classes = [JWTAuthentication]


    # ========================================================
    # PERMISOS
    # ========================================================

    # IsAuthenticated significa que solamente los usuarios
    # autenticados pueden utilizar estos endpoints.
    permission_classes = [IsAuthenticated]


    # ========================================================
    # SERVICIO CVU
    # ========================================================

    # Creamos una instancia del servicio.
    #
    # El ViewSet delegará en esta instancia la mayor parte de
    # la lógica relacionada con el CVU.
    service = CVUService()


    # ========================================================
    # MÉTODOS HTTP PERMITIDOS
    # ========================================================

    # Este ViewSet únicamente permite:
    #
    # POST
    # GET
    # PATCH
    #
    # No permite DELETE directamente desde este ViewSet.
    http_method_names = ["post", "get", "patch"]


    # ========================================================
    # OBTENER CVU DE UN USUARIO
    # ========================================================

    def retrieve(self, request, pk, *args, **kwargs):
        """
        Obtiene el CVU completo de un usuario específico.

        El parámetro "pk" corresponde al ID del usuario.

        Ejemplo:

            GET /api/v1/cvu/UUID/

        El método obtiene:

        1. El usuario.
        2. Los productos de investigador.
        3. El perfil del usuario.
        4. Construye la respuesta que será enviada al frontend.
        """

        # ----------------------------------------------------
        # BUSCAR USUARIO
        # ----------------------------------------------------
        #
        # "pk" viene directamente de la URL.
        #
        # Se busca un usuario cuyo ID sea igual al recibido.
        user_instance = User.objects.filter(id=pk).first()


        # ----------------------------------------------------
        # VALIDAR QUE EL USUARIO EXISTA
        # ----------------------------------------------------

        if not user_instance:

            return Response(
                {
                    "message": "Usuario no encontrado."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


        # ----------------------------------------------------
        # OBTENER PRODUCTOS DEL INVESTIGADOR
        # ----------------------------------------------------
        #
        # Se solicita al servicio todos los productos CVU
        # asociados con el usuario.
        cvu_data = self.service.get_productos_investigador(
            user_instance.id
        )


        # ----------------------------------------------------
        # OBTENER PERFIL DEL USUARIO
        # ----------------------------------------------------
        #
        # Además de los productos, obtenemos los datos personales
        # y académicos almacenados en PerfilUsuario.
        user_data = self.service.get_perfil_usuario(
            user_instance.id
        )


        # ----------------------------------------------------
        # VALIDAR RESULTADO DEL PERFIL
        # ----------------------------------------------------

        if user_data.is_err():

            # ------------------------------------------------
            # PERFIL NO ENCONTRADO
            # ------------------------------------------------
            #
            # Si el error específicamente corresponde a
            # NOT_FOUND, devolvemos 404.
            if user_data.get_error().code == ErrorCode.NOT_FOUND:

                return Response(
                    {
                        "message": "Perfil de usuario no encontrado."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )


            # ------------------------------------------------
            # OTRO ERROR
            # ------------------------------------------------
            #
            # Si ocurrió otro problema al obtener el perfil,
            # devolvemos el mensaje del error.
            return Response(
                {
                    "message": user_data.get_error().message
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


        # ----------------------------------------------------
        # RESPUESTA EXITOSA
        # ----------------------------------------------------
        #
        # asdict convierte el DTO del perfil en un diccionario
        # que puede ser serializado como JSON.
        return Response(
            {
                "message": "CVU obtenido correctamente",

                # Información del perfil.
                "user_data": asdict(
                    user_data.unwrap()
                ),

                # Productos del investigador.
                "data": cvu_data,
            },
            status=status.HTTP_200_OK,
        )


    # ========================================================
    # CARGAR CVU COMPLETO DESDE ARCHIVO
    # ========================================================

    def create(self, request, *args, **kwargs):
        """
        Recibe un archivo JSON que contiene el CVU completo
        de un investigador.

        El frontend envía:

            cvuFile
            usuario

        Donde:

            cvuFile:
                Archivo JSON.

            usuario:
                UUID del usuario al que se asociará el CVU.

        El método delega el procesamiento real a:

            self.service.read_cvu(...)
        """

        # ----------------------------------------------------
        # OBTENER ARCHIVO
        # ----------------------------------------------------
        #
        # request.FILES contiene los archivos enviados mediante
        # multipart/form-data.
        #
        # CVUUpload.jsx envía el archivo con el nombre:
        #
        # cvuFile
        cvu_file = request.FILES.get("cvuFile")


        # ----------------------------------------------------
        # OBTENER ID DEL USUARIO
        # ----------------------------------------------------
        #
        # request.data contiene los campos enviados en la
        # petición multipart/form-data.
        #
        # El frontend actualmente envía:
        #
        # usuario = userId
        usuario_id = request.data.get("usuario")


        # ----------------------------------------------------
        # BUSCAR USUARIO
        # ----------------------------------------------------
        #
        # El usuario recibido será el propietario de los datos
        # que se van a cargar.
        usuario_instance = User.objects.filter(
            id=usuario_id
        ).first()


        # ----------------------------------------------------
        # VALIDAR USUARIO
        # ----------------------------------------------------

        if not usuario_instance:

            return Response(
                {
                    "message": "Usuario no encontrado."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


        # ----------------------------------------------------
        # REGISTRAR OPERACIÓN EN LOG
        # ----------------------------------------------------
        #
        # request.user es el usuario autenticado mediante JWT.
        #
        # usuario_id es el usuario que recibimos en el campo
        # "usuario".
        #
        # Esto permite detectar una diferencia importante:
        #
        # usuario autenticado
        #        VS
        # usuario destino del CVU
        logger.info(
            f"Usuario {request.user.id} está cargando un CVU "
            f"para el usuario {usuario_id}."
        )


        # ----------------------------------------------------
        # PROCESAR CVU
        # ----------------------------------------------------
        #
        # Aquí comienza realmente el procesamiento del archivo.
        #
        # CVUService:
        #
        # - lee el JSON,
        # - serializa los datos,
        # - extrae el perfil,
        # - guarda/actualiza el perfil,
        # - elimina productos anteriores,
        # - inserta los nuevos productos.
        result = self.service.read_cvu(
            cvu_file,
            investigador_id=usuario_instance.id
        )


        # ----------------------------------------------------
        # VALIDAR RESULTADO
        # ----------------------------------------------------

        if result.is_ok():

            # ------------------------------------------------
            # CARGA EXITOSA
            # ------------------------------------------------
            return Response(
                {
                    "message": "CVU cargado correctamente",
                    "data": result.unwrap(),
                },
                status=status.HTTP_201_CREATED,
            )


        # ----------------------------------------------------
        # ERROR DURANTE LA CARGA
        # ----------------------------------------------------
        #
        # IMPORTANTE:
        #
        # Aquí se utiliza result.unwrap() aunque el Result
        # indica que hubo un error.
        #
        # Dependiendo de la implementación de Result, unwrap()
        # puede lanzar una excepción cuando el resultado es un
        # error.
        #
        # Esto puede provocar que un error que originalmente
        # debería regresar HTTP 400 termine convirtiéndose en
        # HTTP 500.
        #
        # Este punto está directamente relacionado con el error
        # "Request failed with status code 500" que observamos
        # durante las pruebas de carga del CVU.
        error = result.get_error()

        return Response(
            {
                "message": error.message if error else "Error al cargar CVU",
                "code": error.code.value if error else ErrorCode.INVALID_INPUT.value,
                "details": error.details if error else None,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


    # ========================================================
    # CREAR UNA NUEVA ENTRADA CVU
    # ========================================================

    @action(
        detail=False,
        methods=["post"],
        url_path="create-entry"
    )
    def create_entry(self, request, *args, **kwargs):
        """
        Crea una nueva entrada individual en el CVU.

        Este endpoint se utiliza cuando el usuario utiliza
        el formulario dinámico de la aplicación y presiona
        "Agregar".

        El frontend envía:

            {
                "tipo": "...",
                "data": {...}
            }

        El usuario asociado al registro se obtiene de:

            request.user.id

        Es decir, en esta operación NO se utiliza un campo
        "usuario" enviado por el frontend.
        """

        # ----------------------------------------------------
        # OBTENER TIPO DE PRODUCTO
        # ----------------------------------------------------
        #
        # Ejemplos:
        #
        # articulosCientifica
        # capitulosCientifica
        # librosCientifica
        # congresos
        #
        tipo = request.data.get("tipo")


        # ----------------------------------------------------
        # OBTENER DATOS DEL PRODUCTO
        # ----------------------------------------------------
        #
        # Aquí se encuentra la información capturada por
        # DynamicForm / RecursiveForm.
        data = request.data.get("data")


        # ----------------------------------------------------
        # CREAR PRODUCTO
        # ----------------------------------------------------
        #
        # request.user.id representa al usuario autenticado.
        #
        # Por lo tanto, un registro creado manualmente queda
        # asociado automáticamente al usuario que inició sesión.
        result = self.service.create_new_entry(
            data,
            tipo,
            request.user.id
        )


        # ----------------------------------------------------
        # VALIDAR RESULTADO
        # ----------------------------------------------------

        if result.is_err():

            return Response(
                {
                    "message": "Error al crear entrada",

                    # NOTA:
                    # Aquí nuevamente se utiliza unwrap()
                    # sobre un resultado de error.
                    "data": result.unwrap(),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


        # ----------------------------------------------------
        # CREACIÓN EXITOSA
        # ----------------------------------------------------

        return Response(
            {
                "message": "Entrada creada correctamente",
                "data": result.unwrap(),
            },
            status=status.HTTP_201_CREATED,
        )


    # ========================================================
    # ACTUALIZAR UNA ENTRADA CVU
    # ========================================================

    @action(
        detail=False,
        methods=["patch"],
        url_path="update-entry"
    )
    def update_entry(self, request, *args, **kwargs):
        """
        Actualiza una entrada existente del CVU.

        El frontend debe enviar:

            {
                "tipo": "...",
                "data": {...},
                "id": "..."
            }

        El usuario se obtiene de:

            request.user.id

        El servicio posteriormente verifica que el producto
        pertenezca al usuario autenticado.
        """

        # ----------------------------------------------------
        # OBTENER TIPO
        # ----------------------------------------------------
        tipo = request.data.get("tipo")


        # ----------------------------------------------------
        # OBTENER DATOS
        # ----------------------------------------------------
        data = request.data.get("data")


        # ----------------------------------------------------
        # OBTENER ID DEL PRODUCTO
        # ----------------------------------------------------
        #
        # Este es el identificador del producto CVU que se
        # desea modificar.
        id_entry = request.data.get("id")


        # ----------------------------------------------------
        # ACTUALIZAR PRODUCTO
        # ----------------------------------------------------
        #
        # Se utiliza request.user.id para garantizar que la
        # operación se realice sobre el usuario autenticado.
        result = self.service.update_entry(
            id_entry,
            data,
            tipo,
            request.user.id
        )


        # ----------------------------------------------------
        # VALIDAR ERROR
        # ----------------------------------------------------

        if result.is_err():

            return Response(
                {
                    "message":
                        "Error al actualizar el producto de investigador",

                    # Igual que en create(), aquí se intenta
                    # obtener el resultado mediante unwrap().
                    "data": result.unwrap(),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


        # ----------------------------------------------------
        # ACTUALIZACIÓN EXITOSA
        # ----------------------------------------------------

        return Response(
            {
                "message":
                    "Producto de investigador actualizado correctamente",

                # Convertimos el DTO en diccionario.
                "data": asdict(
                    result.unwrap()
                ),
            },
            status=status.HTTP_200_OK,
        )


    # ========================================================
    # OBTENER ESPECIFICACIÓN DE FORMULARIO
    # ========================================================

    @action(
        detail=False,
        methods=["get"],
        url_path="form/(?P<product_type>[^/.]+)"
    )
    def get_form_specifications(
        self,
        request,
        product_type=None,
        *args,
        **kwargs
    ):
        """
        Obtiene la especificación utilizada para construir
        dinámicamente un formulario CVU.

        Ejemplo:

            GET /api/v1/cvu/form/articulosCientifica/

        product_type sería:

            articulosCientifica

        La respuesta contiene la estructura que posteriormente
        consume el frontend para construir DynamicForm /
        RecursiveForm.
        """

        # ----------------------------------------------------
        # VALIDAR TIPO DE PRODUCTO
        # ----------------------------------------------------

        if not product_type:

            return Response(
                {
                    "message":
                        "Tipo de producto no proporcionado."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


        # ----------------------------------------------------
        # BUSCAR TIPO EN CATÁLOGO
        # ----------------------------------------------------
        #
        # CatalogoProducto contiene los tipos de productos
        # disponibles para el CVU.
        type_instance = CatalogoProducto.objects.filter(
            nombre=product_type
        ).first()


        # ----------------------------------------------------
        # VALIDAR TIPO
        # ----------------------------------------------------

        if not type_instance:

            return Response(
                {
                    "message":
                        "Tipo de producto no válido."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


        # ----------------------------------------------------
        # OBTENER FORMULARIO DESDE EL SERVICIO
        # ----------------------------------------------------
        #
        # CVUService se encarga de construir/obtener la
        # especificación correspondiente al tipo solicitado.
        form_data = self.service.get_form_data(
            product_type
        )


        # ----------------------------------------------------
        # DEVOLVER ESPECIFICACIÓN
        # ----------------------------------------------------
        #
        # El frontend utiliza esta información para construir
        # el formulario dinámicamente.
        return Response(
            form_data,
            status=status.HTTP_200_OK
        )