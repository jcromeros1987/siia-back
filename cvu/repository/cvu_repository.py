# ============================================================
# IMPORTACIONES
# ============================================================

# Iterable permite indicar que una función puede devolver
# cualquier objeto iterable, por ejemplo una lista, tupla,
# QuerySet, etc.
from typing import Iterable


# UUID representa los identificadores únicos utilizados por
# los usuarios y productos.
from uuid import UUID


# transaction.atomic permite ejecutar una operación dentro de
# una transacción de base de datos.
#
# Si ocurre un error dentro de una operación atómica, Django
# puede revertir los cambios realizados durante esa transacción.
from django.db import transaction


# QuerySet representa el conjunto de resultados que devuelve
# Django ORM cuando realizamos consultas sobre los modelos.
from django.db.models import QuerySet


# Logger utilizado para registrar información importante
# durante las operaciones del repositorio.
from cvu.logger import logger


# DTO que representa un tipo de producto del catálogo.
#
# DTO de perfil utilizado para transportar la información
# del perfil del investigador.
from cvu.DTOs import (
    CatalogoProductoDTO,
    PerfilUsuarioDTO
)


# DTOs relacionados con los productos del investigador.
#
# ProductoInvestigadorCheckerDTO:
#   Contiene información utilizada para consultar/verificar
#   productos.
#
# ProductoInvestigadorDTO:
#   Contiene información más completa del producto.
from cvu.DTOs.producto_investigador_dto import (
    ProductoInvestigadorCheckerDTO,
    ProductoInvestigadorDTO,
)


# Modelos de Django utilizados por este repositorio.
#
# CatalogoProducto:
#   Catálogo de tipos de productos CVU.
#
# User:
#   Usuario/investigador.
#
# ProductoInvestigador:
#   Producto registrado dentro del CVU.
#
# PerfilUsuario:
#   Perfil personal/académico del investigador.
from cvu.models import (
    CatalogoProducto,
    User,
    ProductoInvestigador,
    PerfilUsuario
)


# Serializers utilizados para validar y guardar información.
#
# ProductoInvestigadorRegisterSerializer:
#   Valida productos.
#
# PerfilUsuarioRegisterSerializer:
#   Valida información del perfil.
from cvu.serializers import (
    ProductoInvestigadorRegisterSerializer,
    PerfilUsuarioRegisterSerializer,
)


# Result:
#   Permite devolver resultados exitosos o errores.
#
# ErrorCode:
#   Contiene los diferentes códigos de error utilizados
#   por la aplicación.
from cvu.utils import Result, ErrorCode


# ============================================================
# REPOSITORIO DEL CVU
# ============================================================

class CVURepository:
    """
    Repositorio encargado de realizar las operaciones de acceso
    a datos del módulo CVU.

    Esta clase es la capa que se encuentra más cerca de la
    base de datos dentro de la arquitectura del módulo.

    Flujo general:

        CVUView
            |
            v
        CVUService
            |
            v
        CVURepository
            |
            v
        Django ORM
            |
            v
        PostgreSQL


    Responsabilidades principales:

    - Consultar el catálogo de productos.
    - Consultar productos de investigadores.
    - Crear productos.
    - Actualizar productos.
    - Eliminar/desactivar productos.
    - Crear o actualizar perfiles.
    - Obtener perfiles.
    - Eliminar perfiles.
    """


    # ========================================================
    # OBTENER CATÁLOGO COMPLETO DE PRODUCTOS
    # ========================================================

    def get_catalogo_productos(
        self
    ) -> Result[Iterable[CatalogoProductoDTO]]:
        """
        Obtiene todos los tipos de productos disponibles
        en el catálogo.

        El catálogo se encuentra en el modelo:

            CatalogoProducto

        El método convierte cada registro del modelo a un DTO.

        Returns:
            Result:
                Resultado exitoso que contiene una tupla de
                CatalogoProductoDTO.
        """

        # ----------------------------------------------------
        # CONSULTAR TODOS LOS TIPOS DE PRODUCTO
        # ----------------------------------------------------

        instances = CatalogoProducto.objects.all()


        # ----------------------------------------------------
        # CONVERTIR MODELOS A DTOs
        # ----------------------------------------------------
        #
        # Cada instancia de CatalogoProducto se convierte
        # mediante su método to_dto().
        #
        # tuple() convierte el resultado en una tupla.

        return Result.ok(
            tuple(
                instance.to_dto()
                for instance in instances
            )
        )


    # ========================================================
    # OBTENER UN PRODUCTO DEL CATÁLOGO
    # ========================================================

    def get_catalogo_producto(
        self,
        tipo: str
    ) -> Result[CatalogoProductoDTO]:
        """
        Obtiene un tipo específico de producto del catálogo.

        Ejemplo:

            tipo = "articulosCientifica"

        Busca el registro cuyo campo "nombre" coincide
        exactamente con el valor recibido.
        """

        # ----------------------------------------------------
        # BUSCAR TIPO DE PRODUCTO
        # ----------------------------------------------------

        instance = (
            CatalogoProducto.objects
            .filter(nombre=tipo)
            .first()
        )


        # ----------------------------------------------------
        # VALIDAR EXISTENCIA
        # ----------------------------------------------------

        if not instance:

            return Result.err_from(
                ErrorCode.NOT_FOUND,
                "Tipo de producto no encontrado"
            )


        # ----------------------------------------------------
        # DEVOLVER DTO
        # ----------------------------------------------------

        return Result.ok(
            instance.to_dto()
        )


    # ========================================================
    # CREAR PRODUCTO DE INVESTIGADOR
    # ========================================================

    @transaction.atomic
    def create_producto_investigador(
        self,
        contenido: dict,
        tipo: str,
        investigador_id: UUID,
        is_from_file: bool
    ) -> Result[dict]:
        """
        Crea un producto para un investigador.

        Este método se utiliza principalmente para productos
        creados individualmente desde el formulario.

        Parámetros:

            contenido:
                Información completa del producto.

            tipo:
                Tipo de producto.

            investigador_id:
                Usuario propietario del producto.

            is_from_file:
                Indica si el producto proviene de un archivo CVU.

                True:
                    producto importado desde archivo.

                False:
                    producto creado manualmente.
        """

        # ----------------------------------------------------
        # BUSCAR INVESTIGADOR
        # ----------------------------------------------------

        investigador = (
            User.objects
            .filter(id=investigador_id)
            .first()
        )


        # ----------------------------------------------------
        # VALIDAR INVESTIGADOR
        # ----------------------------------------------------

        if not investigador:

            return Result.err_from(
                ErrorCode.NOT_FOUND,
                "Investigador no encontrado"
            )


        # ----------------------------------------------------
        # BUSCAR TIPO DE PRODUCTO
        # ----------------------------------------------------

        tipo_instance = (
            CatalogoProducto.objects
            .filter(nombre=tipo)
            .first()
        )


        # ----------------------------------------------------
        # PREPARAR DATOS PARA SERIALIZER
        # ----------------------------------------------------

        insert_data = {

            # Contenido JSON del producto.
            "contenido": contenido,

            # ID del tipo de producto.
            "tipo": tipo_instance.id,

            # ID del investigador.
            "investigador": investigador.id,

            # Indicar si proviene de archivo.
            "is_from_file": is_from_file,
        }


        # ----------------------------------------------------
        # CREAR SERIALIZER
        # ----------------------------------------------------
        #
        # El serializer será responsable de validar la
        # información antes de guardarla.

        serializer = ProductoInvestigadorRegisterSerializer(
            data=insert_data
        )


        # ----------------------------------------------------
        # VALIDAR DATOS
        # ----------------------------------------------------

        if not serializer.is_valid():

            return Result.err_from(
                ErrorCode.VALIDATION_ERROR,
                "Error de validación",
                serializer.errors
            )


        # ----------------------------------------------------
        # GUARDAR
        # ----------------------------------------------------

        serializer.save()


        # ----------------------------------------------------
        # DEVOLVER PRODUCTO CREADO
        # ----------------------------------------------------

        return Result.ok(
            serializer.data
        )


    # ========================================================
    # OBTENER UN PRODUCTO DE UN INVESTIGADOR
    # ========================================================

    def get_producto_investigador(
        self,
        id_producto: UUID,
        investigador_id: UUID
    ) -> Result[ProductoInvestigadorCheckerDTO]:
        """
        Obtiene un producto específico perteneciente a un
        investigador.

        La consulta valida simultáneamente:

            - ID del producto.
            - Investigador propietario.
            - status=True.

        Por lo tanto, un producto desactivado no será encontrado.
        """

        # ----------------------------------------------------
        # BUSCAR INVESTIGADOR
        # ----------------------------------------------------

        investigador = (
            User.objects
            .filter(id=investigador_id)
            .first()
        )


        # ----------------------------------------------------
        # VALIDAR INVESTIGADOR
        # ----------------------------------------------------

        if not investigador:

            return Result.err_from(
                ErrorCode.NOT_FOUND,
                "Investigador no encontrado"
            )


        # ----------------------------------------------------
        # BUSCAR PRODUCTO
        # ----------------------------------------------------
        #
        # El producto debe:
        #
        # 1. Tener el ID solicitado.
        # 2. Pertenecer al investigador.
        # 3. Estar activo.

        instance = (
            ProductoInvestigador.objects
            .filter(
                id=id_producto,
                investigador=investigador,
                status=True
            )
            .first()
        )


        # ----------------------------------------------------
        # VALIDAR PRODUCTO
        # ----------------------------------------------------

        if not instance:

            return Result.err_from(
                ErrorCode.NOT_FOUND,
                "Investigador no encontrado"
            )


        # ----------------------------------------------------
        # DEVOLVER DTO
        # ----------------------------------------------------

        return Result.ok(
            instance.to_checker_dto()
        )


    # ========================================================
    # OBTENER PRODUCTO DE MUESTRA
    # ========================================================

    def get_muestra_producto_investigador(
        self,
        tipo: str
    ) -> Result[ProductoInvestigadorDTO]:
        """
        Obtiene un producto de muestra de un determinado tipo.

        Esta función es utilizada por el servicio para analizar
        la estructura de un producto y generar:

            - especificaciones de display
            - especificaciones de formulario
        """

        # ----------------------------------------------------
        # BUSCAR TIPO DE PRODUCTO
        # ----------------------------------------------------

        tipo_instance = (
            CatalogoProducto.objects
            .filter(nombre=tipo)
            .first()
        )


        # ----------------------------------------------------
        # VALIDAR TIPO
        # ----------------------------------------------------

        if not tipo_instance:

            return Result.err_from(
                ErrorCode.NOT_FOUND,
                "Tipo de producto no encontrado"
            )


        # ----------------------------------------------------
        # BUSCAR PRODUCTO DE MUESTRA
        # ----------------------------------------------------
        #
        # Se obtiene el primer producto activo de ese tipo.

        instance = (
            ProductoInvestigador.objects
            .filter(
                tipo=tipo_instance,
                status=True
            )
            .first()
        )


        # ----------------------------------------------------
        # VALIDAR MUESTRA
        # ----------------------------------------------------

        if not instance:

            return Result.err_from(
                ErrorCode.NOT_FOUND,
                "No se encontró un producto de muestra "
                "para el tipo especificado"
            )


        # ----------------------------------------------------
        # DEVOLVER DTO
        # ----------------------------------------------------

        return Result.ok(
            instance.to_dto()
        )


    # ========================================================
    # OBTENER PRODUCTOS DE UN INVESTIGADOR
    # ========================================================

    def get_productos_investigador(
        self,
        investigador_id: UUID,
        tipo: str = None,
        status: bool = None,
        is_from_file: bool = None,
        check_dto: bool = True,
    ) -> Result[Iterable[ProductoInvestigadorCheckerDTO]]:
        """
        Obtiene los productos de un investigador.

        Permite aplicar filtros opcionales:

            tipo:
                Filtrar por tipo de producto.

            status:
                Filtrar por estado activo/inactivo.

            is_from_file:
                Filtrar por origen del producto.

            check_dto:
                Determina qué DTO se utiliza para devolver
                la información.
        """

        # ----------------------------------------------------
        # CONSTRUIR FILTROS
        # ----------------------------------------------------

        args = {}


        # ----------------------------------------------------
        # FILTRO STATUS
        # ----------------------------------------------------

        if status is not None:

            args["status"] = status


        # ----------------------------------------------------
        # FILTRO ORIGEN DEL ARCHIVO
        # ----------------------------------------------------

        if is_from_file is not None:

            args["is_from_file"] = is_from_file


        # ----------------------------------------------------
        # FILTRO TIPO
        # ----------------------------------------------------

        if tipo is not None:

            # Buscar tipo en catálogo.
            tipo_instance = (
                CatalogoProducto.objects
                .filter(nombre=tipo)
                .first()
            )


            # Validar que exista.
            if not tipo_instance:

                return Result.err_from(
                    ErrorCode.NOT_FOUND,
                    "Tipo de producto no encontrado"
                )


            # Agregar instancia al filtro.
            args["tipo"] = tipo_instance


        # ----------------------------------------------------
        # OBTENER PRODUCTOS
        # ----------------------------------------------------

        return (
            self._get_productos_investigador(
                investigador_id,
                **args
            )
            .map_value(

                # Convertir cada producto al DTO solicitado.
                lambda productos:
                    tuple(

                        producto.to_checker_dto()
                        if check_dto
                        else producto.to_dto()

                        for producto in productos
                    )
            )
        )


    # ========================================================
    # ELIMINAR PRODUCTOS DEL INVESTIGADOR
    # ========================================================

    @transaction.atomic
    def delete_productos_investigador(
        self,
        investigador_id: UUID,
        status: bool = None,
        is_from_file: bool = None,
        logic: bool = False,
    ) -> Result[str]:
        """
        Elimina productos de un investigador.

        Dependiendo de "logic":

            logic=True
                Se realiza eliminación lógica.

                status=False

            logic=False
                Se realiza eliminación física.

                DELETE FROM tabla

        Esta función está dentro de una transacción atómica.
        """

        # ----------------------------------------------------
        # CONSTRUIR FILTROS
        # ----------------------------------------------------

        args = {}


        # Filtro por status.
        if status is not None:

            args["status"] = status


        # Filtro por origen.
        if is_from_file is not None:

            args["is_from_file"] = is_from_file


        # ----------------------------------------------------
        # FUNCIÓN INTERNA DE ELIMINACIÓN
        # ----------------------------------------------------

        def delete_products(
            productos: QuerySet
        ) -> Result[str]:

            # ------------------------------------------------
            # ELIMINACIÓN LÓGICA
            # ------------------------------------------------

            if logic:

                # En lugar de eliminar físicamente los registros,
                # se cambia su status a False.
                productos.update(
                    status=False
                )


            # ------------------------------------------------
            # ELIMINACIÓN FÍSICA
            # ------------------------------------------------

            else:

                # Elimina realmente los registros de la tabla.
                productos.delete()


            # Devolver resultado exitoso.
            return Result.ok(
                "Productos eliminados"
            )


        # ----------------------------------------------------
        # OBTENER Y ELIMINAR
        # ----------------------------------------------------

        return (
            self._get_productos_investigador(
                investigador_id,
                **args
            )
            .and_then(
                delete_products
            )
        )


    # ========================================================
    # ACTUALIZAR PRODUCTO
    # ========================================================

    @transaction.atomic
    def update_producto_investigador(
        self,
        id_producto: UUID,
        investigador_id: UUID,
        data: dict,
        eje: str,
        titulo: str,
    ) -> Result[ProductoInvestigadorCheckerDTO]:
        """
        Actualiza un producto existente.

        La búsqueda valida:

            - ID del producto.
            - Investigador propietario.
            - status=True.
        """

        # ----------------------------------------------------
        # BUSCAR PRODUCTO
        # ----------------------------------------------------

        instance = (
            ProductoInvestigador.objects
            .filter(
                id=id_producto,
                investigador=investigador_id,
                status=True
            )
            .first()
        )


        # ----------------------------------------------------
        # VALIDAR PRODUCTO
        # ----------------------------------------------------

        if not instance:

            return Result.err_from(
                ErrorCode.NOT_FOUND,
                "Investigador no encontrado"
            )


        # ----------------------------------------------------
        # ACTUALIZAR EJE
        # ----------------------------------------------------

        instance.eje = eje


        # ----------------------------------------------------
        # ACTUALIZAR TÍTULO
        # ----------------------------------------------------

        instance.titulo = titulo


        # ----------------------------------------------------
        # ACTUALIZAR CONTENIDO
        # ----------------------------------------------------

        instance.contenido = data


        # ----------------------------------------------------
        # GUARDAR CAMBIOS
        # ----------------------------------------------------

        instance.save()


        # ----------------------------------------------------
        # DEVOLVER DTO
        # ----------------------------------------------------

        return Result.ok(
            instance.to_checker_dto()
        )


    # ========================================================
    # INSERTAR PRODUCTOS DEL CVU
    # ========================================================

    def insert_productos_investigador(
        self,
        productos: dict,
        investigador_id: UUID
    ) -> Result[str]:
        """
        Inserta los productos obtenidos desde un archivo CVU.

        Este método es utilizado durante la importación completa
        del CVU.

        El flujo es:

            productos del JSON
                    |
                    v
            recorrer tipos
                    |
                    v
            obtener catálogo
                    |
                    v
            construir objetos
                    |
                    v
            bulk_create()
                    |
                    v
            PostgreSQL
        """


        # ====================================================
        # FUNCIÓN INTERNA PARA CONSTRUIR PRODUCTOS
        # ====================================================

        def populate_productos_list(
            productos_list: list,
            investigador_instance: User,
            catalogo: CatalogoProductoDTO,
            productos_result: list,
        ) -> Result[list]:
            """
            Convierte los diccionarios de productos en instancias
            del modelo ProductoInvestigador.

            Las instancias no se guardan individualmente aquí.

            Se acumulan en productos_result para posteriormente
            utilizar bulk_create().
            """

            # ------------------------------------------------
            # OBTENER INSTANCIA REAL DEL CATÁLOGO
            # ------------------------------------------------

            catalogo_instance = (
                CatalogoProducto.objects
                .filter(
                    nombre=catalogo.nombre
                )
                .first()
            )


            # ------------------------------------------------
            # RECORRER PRODUCTOS
            # ------------------------------------------------

            for producto_data in productos_list:

                # Crear objeto ProductoInvestigador.
                productos_result.append(

                    ProductoInvestigador(

                        # ID proveniente del JSON CVU.
                        id_producto=
                            producto_data.get("id"),

                        # Eje.
                        eje=
                            producto_data.get("eje"),

                        # Título.
                        titulo=
                            producto_data.get("titulo"),

                        # Contenido completo.
                        contenido=
                            producto_data.get("contenido"),

                        # Tipo de producto.
                        tipo=
                            catalogo_instance,

                        # Investigador propietario.
                        investigador=
                            investigador_instance,

                        # El producto proviene de un archivo.
                        is_from_file=True,
                    )
                )


            # ------------------------------------------------
            # DEVOLVER LISTA
            # ------------------------------------------------

            return Result.ok(
                productos_result
            )


        # ====================================================
        # REGISTRAR OPERACIÓN
        # ====================================================

        logger.info(
            f"Inserting productos for investigador_id: "
            f"{investigador_id}"
        )


        # Lista donde se acumularán todos los productos
        # antes del bulk_create().
        nuevos_productos = []


        # ====================================================
        # BUSCAR INVESTIGADOR
        # ====================================================

        investigador = (
            User.objects
            .filter(id=investigador_id)
            .first()
        )


        # ----------------------------------------------------
        # VALIDAR INVESTIGADOR
        # ----------------------------------------------------

        if not investigador:

            return Result.err_from(
                ErrorCode.NOT_FOUND,
                "Investigador no encontrado"
            )


        # ====================================================
        # RECORRER TIPOS DE PRODUCTOS
        # ====================================================

        for tipo, producto_list in productos.items():

            # Obtener tipo del catálogo y, si existe,
            # agregar sus productos a la lista.
            self.get_catalogo_producto(
                tipo
            ).and_then(

                lambda catalogo:
                    populate_productos_list(
                        producto_list,
                        investigador,
                        catalogo,
                        nuevos_productos
                    )
            )


        # ====================================================
        # INSERTAR EN BLOQUE
        # ====================================================
        #
        # bulk_create() permite insertar muchos registros
        # utilizando una operación optimizada en lugar de
        # realizar un INSERT individual por cada producto.

        ProductoInvestigador.objects.bulk_create(
            nuevos_productos
        )


        # ====================================================
        # RESULTADO
        # ====================================================

        return Result.ok(
            "Productos de investigador insertados correctamente."
        )


    # ========================================================
    # CONSULTA INTERNA DE PRODUCTOS
    # ========================================================

    def _get_productos_investigador(
        self,
        investigador_id: UUID,
        **kwargs: dict
    ) -> Result[QuerySet]:
        """
        Método interno utilizado para obtener los productos
        de un investigador.

        kwargs contiene filtros adicionales.

        Ejemplo:

            status=True

        o:

            status=True,
            is_from_file=True

        o:

            tipo=<CatalogoProducto>
        """

        # ----------------------------------------------------
        # BUSCAR INVESTIGADOR
        # ----------------------------------------------------

        investigador = (
            User.objects
            .filter(id=investigador_id)
            .first()
        )


        # ----------------------------------------------------
        # VALIDAR INVESTIGADOR
        # ----------------------------------------------------

        if not investigador:

            return Result.err_from(
                ErrorCode.NOT_FOUND,
                "Investigador no encontrado"
            )


        # ----------------------------------------------------
        # BUSCAR PRODUCTOS
        # ----------------------------------------------------
        #
        # Se utiliza el investigador como condición obligatoria
        # y se agregan los filtros recibidos en kwargs.

        productos = (
            ProductoInvestigador.objects
            .filter(
                investigador=investigador,
                **kwargs
            )
        )


        # ----------------------------------------------------
        # DEVOLVER QUERYSET
        # ----------------------------------------------------

        return Result.ok(
            productos
        )


    # ========================================================
    # CREAR O ACTUALIZAR PERFIL
    # ========================================================

    @transaction.atomic
    def create_or_update_perfil_usuario(
        self,
        investigador_id: UUID,
        data: dict
    ) -> Result[PerfilUsuarioDTO]:
        """
        Crea o actualiza el perfil de un investigador.

        Si el investigador ya tiene un PerfilUsuario:

            -> se actualiza.

        Si todavía no tiene:

            -> se crea.

        La validación se realiza mediante
        PerfilUsuarioRegisterSerializer.
        """

        # ----------------------------------------------------
        # BUSCAR INVESTIGADOR
        # ----------------------------------------------------

        investigador = (
            User.objects
            .filter(id=investigador_id)
            .first()
        )


        # ----------------------------------------------------
        # VALIDAR INVESTIGADOR
        # ----------------------------------------------------

        if not investigador:

            return Result.err_from(
                ErrorCode.NOT_FOUND,
                "Investigador no encontrado"
            )


        # ----------------------------------------------------
        # ASOCIAR PERFIL CON USUARIO
        # ----------------------------------------------------
        #
        # Se agrega explícitamente el ID del usuario al
        # diccionario que será enviado al serializer.

        data["usuario"] = investigador.id


        # ----------------------------------------------------
        # BUSCAR PERFIL EXISTENTE
        # ----------------------------------------------------

        perfil = (
            PerfilUsuario.objects
            .filter(
                usuario=investigador
            )
            .first()
        )


        # ----------------------------------------------------
        # CREAR SERIALIZER
        # ----------------------------------------------------
        #
        # Si "perfil" existe, el serializer actualizará ese
        # registro.
        #
        # Si "perfil" es None, se creará uno nuevo.

        serializer = PerfilUsuarioRegisterSerializer(
            perfil,
            data=data,
            partial=True
        )


        # ----------------------------------------------------
        # VALIDAR
        # ----------------------------------------------------

        if not serializer.is_valid():

            return Result.err_from(
                ErrorCode.VALIDATION_ERROR,
                "Error de validación",
                serializer.errors
            )


        # ----------------------------------------------------
        # GUARDAR PERFIL
        # ----------------------------------------------------

        saved_perfil = serializer.save()


        # ----------------------------------------------------
        # CONVERTIR A DTO
        # ----------------------------------------------------

        return Result.ok(
            self._perfil_to_dto(
                saved_perfil
            )
        )


    # ========================================================
    # VALIDAR USUARIO DEL CVU
    # ========================================================

    def validate_cvu_usuario_id(
        self,
        investigador_id: UUID,
        cvu_usuario_id: str
    ) -> Result[bool]:
        """
        Valida que el usuario_id incluido en el archivo CVU
        corresponda al usuario propietario del perfil en BD.

        La validación se realiza exclusivamente contra:

            app_cvu.cvu_perfil_usuarios.usuario_id

        utilizando investigador_id para localizar el perfil que
        pertenece al usuario al que se está realizando la carga.
        """

        if not cvu_usuario_id:

            return Result.err_from(
                ErrorCode.VALIDATION_ERROR,
                "El archivo CVU no contiene el usuario_id requerido para la validación."
            )

        perfil = (
            PerfilUsuario.objects
            .filter(
                usuario=investigador_id,
                usuario_id=cvu_usuario_id
            )
            .first()
        )

        if not perfil:

            return Result.err_from(
                ErrorCode.VALIDATION_ERROR,
                "No se puede cargar el CVU porque el usuario_id del archivo no corresponde al usuario registrado."
            )

        return Result.ok(True)

        # ========================================================
    # VALIDAR DATOS PERSONALES DEL CVU
    # ========================================================

    def validate_cvu_datos_personales(
        self,
        investigador_id: UUID,
        cvu_usuario_id: str,
        nombre: str,
        primer_apellido: str = None,
        segundo_apellido: str = None,
    ) -> Result[bool]:
        """
        Valida los cuatro datos de identidad del JSON CVU
        contra el perfil precargado en la base de datos.

        Comparación:

            JSON.usuario_id
                ↔
            BD.usuario_id

            JSON.perfil.principal.nombre
                ↔
            BD.nombre

            JSON.perfil.principal.primerApellido
                ↔
            BD.primer_apellido

            JSON.perfil.principal.segundoApellido
                ↔
            BD.segundo_apellido

        Regla:

            Los cuatro valores deben coincidir.
            Si uno solo no coincide, la carga es rechazada.

        Este método solamente valida información.
        No realiza INSERT, UPDATE ni DELETE.
        """

        # ----------------------------------------------------
        # NORMALIZAR DATOS RECIBIDOS DEL JSON
        # ----------------------------------------------------

        usuario_id_cvu = (
            str(cvu_usuario_id).strip().casefold()
            if cvu_usuario_id is not None
            else ""
        )

        nombre_cvu = (
            str(nombre).strip().casefold()
            if nombre is not None
            else ""
        )

        primer_apellido_cvu = (
            str(primer_apellido).strip().casefold()
            if primer_apellido is not None
            else ""
        )

        segundo_apellido_cvu = (
            str(segundo_apellido).strip().casefold()
            if segundo_apellido is not None
            else ""
        )

        # ----------------------------------------------------
        # VALIDAR DATOS OBLIGATORIOS DEL JSON
        # ----------------------------------------------------

        if not usuario_id_cvu:
            return Result.err_from(
                ErrorCode.VALIDATION_ERROR,
                "El archivo CVU no contiene el usuario_id requerido "
                "para la validación.",
            )

        if not nombre_cvu:
            return Result.err_from(
                ErrorCode.VALIDATION_ERROR,
                "El archivo CVU no contiene el nombre requerido "
                "para la validación.",
            )

        if not primer_apellido_cvu:
            return Result.err_from(
                ErrorCode.VALIDATION_ERROR,
                "El archivo CVU no contiene el primer apellido requerido "
                "para la validación.",
            )

        if not segundo_apellido_cvu:
            return Result.err_from(
                ErrorCode.VALIDATION_ERROR,
                "El archivo CVU no contiene el segundo apellido requerido "
                "para la validación.",
            )

        # ----------------------------------------------------
        # BUSCAR PERFIL PRECARGADO EN LA BASE DE DATOS
        # ----------------------------------------------------

        perfil = (
            PerfilUsuario.objects
            .filter(
                usuario=investigador_id,
                usuario_id=cvu_usuario_id,
            )
            .first()
        )

        # ----------------------------------------------------
        # VALIDAR EXISTENCIA DEL PERFIL
        # ----------------------------------------------------

        if not perfil:
            return Result.err_from(
                ErrorCode.VALIDATION_ERROR,
                "No se encontró un perfil precargado que corresponda "
                "al usuario_id del archivo CVU.",
            )

        # ----------------------------------------------------
        # NORMALIZAR DATOS REGISTRADOS EN BD
        # ----------------------------------------------------

        usuario_id_bd = (
            str(perfil.usuario_id).strip().casefold()
            if perfil.usuario_id is not None
            else ""
        )

        nombre_bd = (
            str(perfil.nombre).strip().casefold()
            if perfil.nombre is not None
            else ""
        )

        primer_apellido_bd = (
            str(perfil.primer_apellido).strip().casefold()
            if perfil.primer_apellido is not None
            else ""
        )

        segundo_apellido_bd = (
            str(perfil.segundo_apellido).strip().casefold()
            if perfil.segundo_apellido is not None
            else ""
        )

        # ----------------------------------------------------
        # VALIDAR QUE BD TENGA LOS CUATRO DATOS
        # ----------------------------------------------------

        if not usuario_id_bd:
            return Result.err_from(
                ErrorCode.VALIDATION_ERROR,
                "El perfil registrado no contiene usuario_id "
                "para realizar la validación.",
            )

        if not nombre_bd:
            return Result.err_from(
                ErrorCode.VALIDATION_ERROR,
                "El perfil registrado no contiene nombre "
                "para realizar la validación.",
            )

        if not primer_apellido_bd:
            return Result.err_from(
                ErrorCode.VALIDATION_ERROR,
                "El perfil registrado no contiene primer apellido "
                "para realizar la validación.",
            )

        if not segundo_apellido_bd:
            return Result.err_from(
                ErrorCode.VALIDATION_ERROR,
                "El perfil registrado no contiene segundo apellido "
                "para realizar la validación.",
            )

        # ----------------------------------------------------
        # COMPARAR LOS CUATRO DATOS DE IDENTIDAD
        # ----------------------------------------------------
        #
        # JSON                       BD
        # ----------------------------------------------------
        # usuario_id       --------> usuario_id
        # nombre           --------> nombre
        # primerApellido   --------> primer_apellido
        # segundoApellido  --------> segundo_apellido
        #
        # Los cuatro valores deben coincidir.

        identidad_coincide = (
            usuario_id_cvu == usuario_id_bd
            and nombre_cvu == nombre_bd
            and primer_apellido_cvu == primer_apellido_bd
            and segundo_apellido_cvu == segundo_apellido_bd
        )

        # ----------------------------------------------------
        # RECHAZAR SI ALGÚN DATO NO COINCIDE
        # ----------------------------------------------------

        if not identidad_coincide:
            logger.warning(
                "Carga de CVU rechazada por diferencia en datos "
                "de identidad. investigador_id=%s, cvu_usuario_id=%s",
                investigador_id,
                cvu_usuario_id,
            )

            return Result.err_from(
                ErrorCode.VALIDATION_ERROR,
                "No se puede cargar el CVU porque los datos de identidad "
                "del archivo no coinciden con los datos registrados.",
            )

        # ----------------------------------------------------
        # VALIDACIÓN CORRECTA
        # ----------------------------------------------------
        #
        # Los cuatro datos coinciden.
        #
        # Este método no modifica ningún registro.

        return Result.ok(True)

    # ========================================================
    # OBTENER PERFIL DE USUARIO
    # ========================================================

    def get_perfil_usuario(
        self,
        investigador_id: UUID
    ) -> Result[PerfilUsuarioDTO]:
        """
        Obtiene el PerfilUsuario correspondiente a un
        investigador.
        """

        # ----------------------------------------------------
        # BUSCAR INVESTIGADOR
        # ----------------------------------------------------

        investigador = (
            User.objects
            .filter(id=investigador_id)
            .first()
        )


        # ----------------------------------------------------
        # VALIDAR INVESTIGADOR
        # ----------------------------------------------------

        if not investigador:

            return Result.err_from(
                ErrorCode.NOT_FOUND,
                "Investigador no encontrado"
            )


        # ----------------------------------------------------
        # BUSCAR PERFIL
        # ----------------------------------------------------

        perfil = (
            PerfilUsuario.objects
            .filter(
                usuario=investigador
            )
            .first()
        )


        # ----------------------------------------------------
        # VALIDAR PERFIL
        # ----------------------------------------------------

        if not perfil:

            return Result.err_from(
                ErrorCode.NOT_FOUND,
                "Perfil de usuario no encontrado"
            )


        # ----------------------------------------------------
        # CONVERTIR A DTO
        # ----------------------------------------------------

        return Result.ok(
            self._perfil_to_dto(
                perfil
            )
        )


    # ========================================================
    # ELIMINAR PERFIL
    # ========================================================

    def delete_perfil_usuario(
        self,
        investigador_id: UUID
    ) -> Result[str]:
        """
        Elimina físicamente el perfil del investigador.
        """

        # ----------------------------------------------------
        # BUSCAR INVESTIGADOR
        # ----------------------------------------------------

        investigador = (
            User.objects
            .filter(id=investigador_id)
            .first()
        )


        # ----------------------------------------------------
        # VALIDAR INVESTIGADOR
        # ----------------------------------------------------

        if not investigador:

            return Result.err_from(
                ErrorCode.NOT_FOUND,
                "Investigador no encontrado"
            )


        # ----------------------------------------------------
        # BUSCAR PERFIL
        # ----------------------------------------------------

        perfil = (
            PerfilUsuario.objects
            .filter(
                usuario=investigador
            )
            .first()
        )


        # ----------------------------------------------------
        # VALIDAR PERFIL
        # ----------------------------------------------------

        if not perfil:

            return Result.err_from(
                ErrorCode.NOT_FOUND,
                "Perfil de usuario no encontrado"
            )


        # ----------------------------------------------------
        # ELIMINAR PERFIL
        # ----------------------------------------------------

        perfil.delete()


        # ----------------------------------------------------
        # RESULTADO
        # ----------------------------------------------------

        return Result.ok(
            "Perfil eliminado"
        )


    # ========================================================
    # CONVERTIR PERFIL A DTO
    # ========================================================

    def _perfil_to_dto(
        self,
        perfil: PerfilUsuario
    ) -> PerfilUsuarioDTO:
        """
        Convierte una instancia del modelo PerfilUsuario
        en un PerfilUsuarioDTO.

        También transforma la información de fotografía
        almacenada en diferentes columnas del modelo en un
        único diccionario.
        """

        # ----------------------------------------------------
        # FOTOGRAFÍA
        # ----------------------------------------------------

        fotografia = None


        # Si existe una URI de fotografía, construimos
        # el objeto correspondiente.
        if perfil.fotografia_uri:

            fotografia = {

                # Nombre del archivo.
                "nombre":
                    perfil.fotografia_nombre,

                # Tipo MIME.
                "contentType":
                    perfil.fotografia_content_type,

                # URI donde se encuentra la fotografía.
                "uri":
                    perfil.fotografia_uri,
            }


        # ====================================================
        # CONSTRUIR DTO
        # ====================================================

        return PerfilUsuarioDTO(

            # ID del perfil.
            id=
                perfil.id,

            # ID del usuario propietario.
            usuario_id=
                perfil.usuario.id,

            # Número CVU.
            cvu=
                perfil.cvu,

            # Nivel académico.
            nivel_academico=
                perfil.nivel_academico,

            # Título.
            titulo=
                perfil.titulo,

            # Nombre.
            nombre=
                perfil.nombre,

            # Primer apellido.
            primer_apellido=
                perfil.primer_apellido,

            # Segundo apellido.
            segundo_apellido=
                perfil.segundo_apellido,

            # Fotografía.
            fotografia=
                fotografia,

            # Semblanza.
            semblanza=
                perfil.semblanza,

            # LinkedIn.
            linkedin=
                perfil.linkedin,

            # ORCID.
            orcid=
                perfil.orcid,

            # Correo alternativo.
            correo_alternativo=
                perfil.correo_alternativo,

            # CURP.
            curp=
                perfil.curp,

            # RFC.
            rfc=
                perfil.rfc,

            # Fecha de nacimiento.
            #
            # Si existe, se convierte a ISO.
            fecha_nacimiento=
                perfil.fecha_nacimiento.isoformat()
                if perfil.fecha_nacimiento
                else None,

            # Intereses.
            #
            # Si el campo es None, se devuelve una lista vacía.
            intereses=
                perfil.intereses or [],

            # Habilidades.
            habilidades=
                perfil.habilidades or [],

            # Sexo.
            sexo=
                perfil.sexo,

            # País de nacimiento.
            pais_nacimiento=
                perfil.pais_nacimiento,

            # Entidad federativa.
            entidad_federativa=
                perfil.entidad_federativa,

            # Estado civil.
            estado_civil=
                perfil.estado_civil,

            # Nacionalidad.
            nacionalidad=
                perfil.nacionalidad,

            # Área de conocimiento.
            area_conocimiento=
                perfil.area_conocimiento,

            # Fecha de creación.
            fecha_creacion=
                perfil.fecha_creacion.isoformat(),

            # Fecha de modificación.
            fecha_modificacion=
                perfil.fecha_modificacion.isoformat(),
        )