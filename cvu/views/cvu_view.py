from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from rest_framework_simplejwt.authentication import JWTAuthentication

from cvu.logger import logger
from cvu.domain import CVUService
from cvu.models import User, CatalogoProducto


class CVUView(ViewSet):
    """
    ViewSet para manejar operaciones relacionadas con el CVU (Currículum Vitae Único) de los usuarios.

    Este ViewSet proporciona endpoints para la gestión completa del CVU de investigadores,
    incluyendo la carga de archivos CVU, creación y actualización de entradas individuales,
    y la obtención de especificaciones de formularios para diferentes tipos de productos académicos.

    Attributes:
        authentication_classes (list): Lista de clases de autenticación. Utiliza autenticación
            basada en cookies (CookieTokenAuthentication).
        permission_classes (list): Lista de clases de permisos requeridos. El usuario debe
            estar autenticado y haber aceptado la política de privacidad.
        service (CVUService): Instancia del servicio CVU para operaciones de negocio.
        http_method_names (list): Métodos HTTP permitidos: POST, GET y PATCH.

    Endpoints:
        - POST /api/cvu/: Carga y procesa un archivo CVU completo.
        - POST /api/cvu/create-entry/: Crea una nueva entrada en el CVU.
        - PATCH /api/cvu/update-entry/: Actualiza una entrada existente en el CVU.
        - GET api/cvu/form/<product_type>/: Obtiene las especificaciones del formulario para un tipo de producto.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    service = CVUService()
    http_method_names = ["post", "get", "patch"]

    def create(self, request, *args, **kwargs):
        """
        Carga y procesa un archivo CVU para un usuario específico.

        Esta función permite cargar un archivo JSON con el CVU completo de un investigador
        y procesarlo para insertar los datos en el sistema.

        Args:
            request (Request): Objeto de solicitud HTTP de Django REST Framework.
                - FILES['cvuFile']: Archivo JSON del CVU a procesar.
                - data['usuario']: ID del usuario al que se asociará el CVU.
            *args: Argumentos posicionales adicionales.
            **kwargs: Argumentos de palabra clave adicionales.

        Returns:
            Response: Respuesta HTTP con el resultado de la operación.
                - 201 CREATED: Si el CVU se procesó correctamente.
                    Formato: {'message': <mensaje de éxito>, 'data': <datos procesados>}
                - 400 BAD REQUEST: Si el usuario no existe o hay error en el procesamiento.
                    Formato: {'message': <mensaje de error>, 'data': <detalle del error>}
        """
        cvu_file = request.FILES.get("cvuFile")
        usuario_id = request.data.get("usuario")
        usuario_instance = User.objects.filter(id=usuario_id).first()
        if not usuario_instance:
            return Response(
                {"message": "Usuario no encontrado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(
            f"Usuario {request.user.id} está cargando un CVU para el usuario {usuario_id}."
        )
        result = self.service.read_cvu(cvu_file, investigador_id=usuario_instance.id)
        if result.is_ok():
            return Response(
                {"message": "CVU cargado correctamente", "data": result.unwrap()},
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"message": "Error al cargar CVU", "data": result.unwrap()},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=False, methods=["post"], url_path="create-entry")
    def create_entry(self, request, *args, **kwargs):
        """
        Crea una nueva entrada en el CVU del usuario autenticado.

        Permite agregar un nuevo registro de producto académico (artículo, capítulo,
        congreso, etc.) al CVU del usuario que realiza la solicitud.

        Args:
            request (Request): Objeto de solicitud HTTP de Django REST Framework.
                - data['tipo']: Tipo de producto académico a crear (ej: 'articulosCientifica',
                    'capitulosCientifica', 'congresos', etc.).
                - data['data']: Diccionario con los datos del producto a crear.
            *args: Argumentos posicionales adicionales.
            **kwargs: Argumentos de palabra clave adicionales.

        Returns:
            Response: Respuesta HTTP con el resultado de la operación.
                - 201 CREATED: Si la entrada se creó correctamente.
                    Formato: {'message': 'Entrada creada correctamente', 'data': <datos creados>}
                - 400 BAD REQUEST: Si hubo un error al crear la entrada.
                    Formato: {'message': 'Error al crear entrada', 'data': <detalle del error>}
        """
        tipo = request.data.get("tipo")
        data = request.data.get("data")
        success, data = self.service.create_new_entry(data, tipo, request.user)
        if success:
            return Response(
                {"message": "Entrada creada correctamente", "data": data},
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"message": "Error al crear entrada", "data": data},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=False, methods=["patch"], url_path="update-entry")
    def update_entry(self, request, *args, **kwargs):
        """
        Actualiza una entrada existente en el CVU del usuario autenticado.

        Permite modificar los datos de un registro de producto académico existente
        en el CVU del usuario.

        Args:
            request (Request): Objeto de solicitud HTTP de Django REST Framework.
                - data['tipo']: Tipo de producto académico a actualizar.
                - data['data']: Diccionario con los nuevos datos del producto.
                - data['id']: Identificador único de la entrada a actualizar.
            *args: Argumentos posicionales adicionales.
            **kwargs: Argumentos de palabra clave adicionales.

        Returns:
            Response: Respuesta HTTP con el resultado de la operación.
                - 200 OK: Si la entrada se actualizó correctamente.
                    Formato: {'message': <mensaje de éxito>, 'data': <datos actualizados>}
                - 400 BAD REQUEST: Si hubo un error al actualizar la entrada.
                    Formato: {'message': <detalle del error>, 'data': None}
        """
        tipo = request.data.get("tipo")
        data = request.data.get("data")
        id_entry = request.data.get("id")

        success, data = self.service.update_entry(id_entry, data, tipo, request.user)
        if success:
            return Response(
                {
                    "message": "Producto de investigador actualizado correctamente",
                    "data": data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "message": "Error al actualizar el producto de investigador",
                "data": data,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=False, methods=["get"], url_path="form/(?P<product_type>[^/.]+)")
    def get_form_specifications(self, request, product_type=None, *args, **kwargs):
        """
        Obtiene las especificaciones del formulario para un tipo de producto académico.

        Retorna la estructura y configuración del formulario necesario para crear
        o editar un tipo específico de producto académico en el CVU.

        Args:
            request (Request): Objeto de solicitud HTTP de Django REST Framework.
            product_type (str, optional): Tipo de producto para el cual se solicitan
                las especificaciones del formulario. Se obtiene de la URL.
                Valores válidos según el catálogo 'Tipo Producto Investigador'.
            *args: Argumentos posicionales adicionales.
            **kwargs: Argumentos de palabra clave adicionales.

        Returns:
            Response: Respuesta HTTP con el resultado de la operación.
                - 200 OK: Si se encontraron las especificaciones del formulario.
                    Formato: Diccionario con la estructura del formulario.
                - 400 BAD REQUEST: Si no se proporcionó el tipo de producto o no es válido.
                    Formato: {'message': <mensaje de error>}
        """
        if not product_type:
            return Response(
                {"message": "Tipo de producto no proporcionado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        type_instance = CatalogoProducto.objects.filter(label=product_type).first()
        if not type_instance:
            return Response(
                {"message": "Tipo de producto no válido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        form_data = self.service.get_form_data(product_type)
        return Response(form_data, status=status.HTTP_200_OK)
