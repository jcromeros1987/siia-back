from typing import Iterable
from uuid import UUID

from django.db import transaction
from django.db.models import QuerySet

from cvu.logger import logger
from cvu.DTOs import CatalogoProductoDTO, PerfilUsuarioDTO
from cvu.DTOs.producto_investigador_dto import (
    ProductoInvestigadorCheckerDTO,
    ProductoInvestigadorDTO,
)
from cvu.models import CatalogoProducto, User, ProductoInvestigador, PerfilUsuario
from cvu.serializers import (
    ProductoInvestigadorRegisterSerializer,
    PerfilUsuarioRegisterSerializer,
)
from cvu.utils import Result, ErrorCode


class CVURepository:
    def get_catalogo_productos(self) -> Result[Iterable[CatalogoProductoDTO]]:
        """
        Retrieves all product types from the catalog. If no products exist, an empty Iterable is returned.

        Returns:
            Result[Iterable[CatalogoProductoDTO]]: A Result object containing:
                - On success: An Iterable of CatalogoProductoDTO objects representing all available
                  product types in the catalog.
                - On failure: An error Result (though this method doesn't currently handle
                  database errors explicitly).
        """
        instances = CatalogoProducto.objects.all()
        return Result.ok(tuple(instance.to_dto() for instance in instances))

    def get_catalogo_producto(self, tipo: str) -> Result[CatalogoProductoDTO]:
        """
        Retrieves a single product type from the catalog by name.

        Args:
            tipo (str): The name of the product type to retrieve.

        Returns:
            Result[CatalogoProductoDTO]: A Result object containing:
                - On success: A CatalogoProductoDTO object for the requested product type.
                - On failure: An error Result with ErrorCode.NOT_FOUND if the product type doesn't exist.
        """
        instance = CatalogoProducto.objects.filter(nombre=tipo).first()
        if not instance:
            return Result.err_from(
                ErrorCode.NOT_FOUND, "Tipo de producto no encontrado"
            )

        return Result.ok(instance.to_dto())

    @transaction.atomic
    def create_producto_investigador(
        self, contenido: dict, tipo: str, investigador_id: UUID, is_from_file: bool
    ) -> Result[dict]:
        """
        Creates a new product for a researcher.

        Args:
            contenido (dict): The product content data.
            tipo (str): The product type name.
            investigador_id (UUID): The researcher's unique identifier.
            is_from_file (bool): Whether the product was created from a file.

        Returns:
            Result[dict]: A Result object containing:
                - On success: A dictionary with the created product data.
                - On failure: An error Result with:
                    - ErrorCode.NOT_FOUND if the researcher doesn't exist.
                    - ErrorCode.VALIDATION_ERROR if the product data is invalid.
        """
        investigador = User.objects.filter(id=investigador_id).first()
        if not investigador:
            return Result.err_from(ErrorCode.NOT_FOUND, "Investigador no encontrado")

        tipo_instance = CatalogoProducto.objects.filter(nombre=tipo).first()
        insert_data = {
            "contenido": contenido,
            "tipo": tipo_instance.id,
            "investigador": investigador.id,
            "is_from_file": is_from_file,
        }
        serializer = ProductoInvestigadorRegisterSerializer(data=insert_data)

        if not serializer.is_valid():
            return Result.err_from(
                ErrorCode.VALIDATION_ERROR, "Error de validación", serializer.errors
            )

        serializer.save()

        return Result.ok(serializer.data)

    def get_producto_investigador(
        self, id_producto: UUID, investigador_id: UUID
    ) -> Result[ProductoInvestigadorCheckerDTO]:
        """
        Retrieves a single product for a researcher.

        Args:
            id_producto (UUID): The product's unique identifier.
            investigador_id (UUID): The researcher's unique identifier.

        Returns:
            Result[ProductoInvestigadorCheckerDTO]: A Result object containing:
                - On success: A ProductoInvestigadorCheckerDTO object for the requested product.
                - On failure: An error Result with ErrorCode.NOT_FOUND if the researcher doesn't exist
                  or the product is not found/inactive.
        """
        investigador = User.objects.filter(id=investigador_id).first()
        if not investigador:
            return Result.err_from(ErrorCode.NOT_FOUND, "Investigador no encontrado")

        instance = ProductoInvestigador.objects.filter(
            id=id_producto, investigador=investigador, status=True
        ).first()
        if not instance:
            return Result.err_from(ErrorCode.NOT_FOUND, "Investigador no encontrado")

        return Result.ok(instance.to_checker_dto())

    def get_muestra_producto_investigador(
        self, tipo: str
    ) -> Result[ProductoInvestigadorDTO]:
        """
        Retrieves a sample product for a given product type.

        Args:
            tipo (str): The product type name.
        Returns:
            Result[ProductoInvestigadorDTO]: A Result object containing:
                - On success: A ProductoInvestigadorDTO object representing a sample product of the specified type.
                - On failure: An error Result with ErrorCode.NOT_FOUND if the product type doesn't exist or no sample product is found.
        """
        tipo_instance = CatalogoProducto.objects.filter(nombre=tipo).first()
        if not tipo_instance:
            return Result.err_from(
                ErrorCode.NOT_FOUND, "Tipo de producto no encontrado"
            )

        instance = ProductoInvestigador.objects.filter(
            tipo=tipo_instance, status=True
        ).first()
        if not instance:
            return Result.err_from(
                ErrorCode.NOT_FOUND,
                "No se encontró un producto de muestra para el tipo especificado",
            )

        return Result.ok(instance.to_dto())

    def get_productos_investigador(
        self,
        investigador_id: UUID,
        tipo: str = None,
        status: bool = None,
        is_from_file: bool = None,
        check_dto: bool = True,
    ) -> Result[Iterable[ProductoInvestigadorCheckerDTO]]:
        """
        Retrieves products for a researcher with optional filtering.

        Args:
            investigador_id: Researcher's unique identifier.
            tipo: Filter by product type name (optional).
            status: Filter by product status (optional).
            is_from_file: Filter by whether product is from a file (optional).
            check_dto: If True, returns ProductoInvestigadorCheckerDTO (minimal fields).
                      If False, returns ProductoInvestigadorDTO (all fields). Defaults to True.

        Returns:
            Result containing an Iterable of product DTOs on success, or an error on failure.
        """
        args = {}
        if status is not None:
            args["status"] = status
        if is_from_file is not None:
            args["is_from_file"] = is_from_file
        if tipo is not None:
            tipo_instance = CatalogoProducto.objects.filter(nombre=tipo).first()
            if not tipo_instance:
                return Result.err_from(
                    ErrorCode.NOT_FOUND, "Tipo de producto no encontrado"
                )
            args["tipo"] = tipo_instance

        return self._get_productos_investigador(investigador_id, **args).map_value(
            lambda productos: tuple(
                producto.to_checker_dto() if check_dto else producto.to_dto()
                for producto in productos
            )
        )

    @transaction.atomic
    def delete_productos_investigador(
        self,
        investigador_id: UUID,
        status: bool = None,
        is_from_file: bool = None,
        logic: bool = False,
    ) -> Result[str]:
        """
        Deletes products for a researcher with optional filtering.

        Args:
            investigador_id (UUID): The researcher's unique identifier.
            status (bool, optional): Filter by product status before deletion. Defaults to None (no filter).
            is_from_file (bool, optional): Filter by whether product is from a file before deletion. Defaults to None (no filter).
            logic (bool, optional): If True, performs soft delete (sets status=False). If False, performs hard delete (removes from database). Defaults to False.

        Returns:
            Result[str]: A Result object containing:
                - On success: A success message "Productos eliminados".
                - On failure: An error Result with ErrorCode.NOT_FOUND if the researcher doesn't exist.
        """
        args = {}
        if status is not None:
            args["status"] = status
        if is_from_file is not None:
            args["is_from_file"] = is_from_file

        def delete_products(productos: QuerySet) -> Result[str]:
            if logic:
                productos.update(status=False)
            else:
                productos.delete()
            return Result.ok("Productos eliminados")

        return self._get_productos_investigador(investigador_id, **args).and_then(
            delete_products
        )

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
        Updates a product for a researcher.

        Args:
            id_producto (UUID): The product's unique identifier.
            investigador_id (UUID): The researcher's unique identifier.
            data (dict): The updated product content data.
            eje (str): The updated product axis/category.
            titulo (str): The updated product title.

        Returns:
            Result[ProductoInvestigadorCheckerDTO]: A Result object containing:
                - On success: A ProductoInvestigadorCheckerDTO object for the updated product.
                - On failure: An error Result with ErrorCode.NOT_FOUND if the product is not found,
                  the researcher doesn't match, or the product is inactive (status=False).
        """
        instance = ProductoInvestigador.objects.filter(
            id=id_producto, investigador=investigador_id, status=True
        ).first()
        if not instance:
            return Result.err_from(ErrorCode.NOT_FOUND, "Investigador no encontrado")

        instance.eje = eje
        instance.titulo = titulo
        instance.contenido = data
        instance.save()

        return Result.ok(instance.to_checker_dto())

    def insert_productos_investigador(
        self, productos: dict, investigador_id: UUID
    ) -> Result[str]:
        def populate_productos_list(
            productos_list: list,
            investigador_instance: User,
            catalogo: CatalogoProductoDTO,
            productos_result: list,
        ) -> Result[list]:
            catalogo_instance = CatalogoProducto.objects.filter(
                nombre=catalogo.nombre
            ).first()
            for producto_data in productos_list:
                productos_result.append(
                    ProductoInvestigador(
                        id_producto=producto_data.get("id"),
                        eje=producto_data.get("eje"),
                        titulo=producto_data.get("titulo"),
                        contenido=producto_data.get("contenido"),
                        tipo=catalogo_instance,
                        investigador=investigador_instance,
                        is_from_file=True,
                    )
                )
            return Result.ok(productos_result)

        logger.info(f"Inserting productos for investigador_id: {investigador_id}")
        nuevos_productos = []
        investigador = User.objects.filter(id=investigador_id).first()
        if not investigador:
            return Result.err_from(ErrorCode.NOT_FOUND, "Investigador no encontrado")

        for tipo, producto_list in productos.items():
            self.get_catalogo_producto(tipo).and_then(
                lambda catalogo: populate_productos_list(
                    producto_list, investigador, catalogo, nuevos_productos
                )
            )

        ProductoInvestigador.objects.bulk_create(nuevos_productos)
        return Result.ok("Productos de investigador insertados correctamente.")

    def _get_productos_investigador(
        self, investigador_id: UUID, **kwargs: dict
    ) -> Result[QuerySet]:
        investigador = User.objects.filter(id=investigador_id).first()
        if not investigador:
            return Result.err_from(ErrorCode.NOT_FOUND, "Investigador no encontrado")

        productos = ProductoInvestigador.objects.filter(
            investigador=investigador, **kwargs
        )

        return Result.ok(productos)

    @transaction.atomic
    def create_or_update_perfil_usuario(
        self, investigador_id: UUID, data: dict
    ) -> Result[PerfilUsuarioDTO]:
        """
        Creates or updates a user profile for a researcher.

        Args:
            investigador_id (UUID): The researcher's unique identifier.
            data (dict): The profile data to save.

        Returns:
            Result[PerfilUsuarioDTO]: A Result object containing:
                - On success: A PerfilUsuarioDTO object for the created/updated profile.
                - On failure: An error Result with ErrorCode.NOT_FOUND if the researcher doesn't exist,
                  or ErrorCode.VALIDATION_ERROR if the data is invalid.
        """
        investigador = User.objects.filter(id=investigador_id).first()
        if not investigador:
            return Result.err_from(ErrorCode.NOT_FOUND, "Investigador no encontrado")

        data["usuario"] = investigador.id

        # Try to get existing profile
        perfil = PerfilUsuario.objects.filter(usuario=investigador).first()

        serializer = PerfilUsuarioRegisterSerializer(perfil, data=data, partial=True)

        if not serializer.is_valid():
            return Result.err_from(
                ErrorCode.VALIDATION_ERROR, "Error de validación", serializer.errors
            )

        saved_perfil = serializer.save()

        return Result.ok(self._perfil_to_dto(saved_perfil))

    def get_perfil_usuario(self, investigador_id: UUID) -> Result[PerfilUsuarioDTO]:
        """
        Retrieves the profile for a researcher.

        Args:
            investigador_id (UUID): The researcher's unique identifier.

        Returns:
            Result[PerfilUsuarioDTO]: A Result object containing:
                - On success: A PerfilUsuarioDTO object for the requested profile.
                - On failure: An error Result with ErrorCode.NOT_FOUND if the researcher or profile doesn't exist.
        """
        investigador = User.objects.filter(id=investigador_id).first()
        if not investigador:
            return Result.err_from(ErrorCode.NOT_FOUND, "Investigador no encontrado")

        perfil = PerfilUsuario.objects.filter(usuario=investigador).first()
        if not perfil:
            return Result.err_from(
                ErrorCode.NOT_FOUND, "Perfil de usuario no encontrado"
            )

        return Result.ok(self._perfil_to_dto(perfil))

    def delete_perfil_usuario(self, investigador_id: UUID) -> Result[str]:
        """
        Deletes the profile for a researcher.

        Args:
            investigador_id (UUID): The researcher's unique identifier.

        Returns:
            Result[str]: A Result object containing:
                - On success: A success message "Perfil eliminado".
                - On failure: An error Result with ErrorCode.NOT_FOUND if the researcher or profile doesn't exist.
        """
        investigador = User.objects.filter(id=investigador_id).first()
        if not investigador:
            return Result.err_from(ErrorCode.NOT_FOUND, "Investigador no encontrado")

        perfil = PerfilUsuario.objects.filter(usuario=investigador).first()
        if not perfil:
            return Result.err_from(
                ErrorCode.NOT_FOUND, "Perfil de usuario no encontrado"
            )

        perfil.delete()
        return Result.ok("Perfil eliminado")

    def _perfil_to_dto(self, perfil: PerfilUsuario) -> PerfilUsuarioDTO:
        """Converts a PerfilUsuario model instance to a DTO."""
        fotografia = None
        if perfil.fotografia_uri:
            fotografia = {
                "nombre": perfil.fotografia_nombre,
                "contentType": perfil.fotografia_content_type,
                "uri": perfil.fotografia_uri,
            }

        return PerfilUsuarioDTO(
            id=perfil.id,
            usuario_id=perfil.usuario.id,
            cvu=perfil.cvu,
            nivel_academico=perfil.nivel_academico,
            titulo=perfil.titulo,
            nombre=perfil.nombre,
            primer_apellido=perfil.primer_apellido,
            segundo_apellido=perfil.segundo_apellido,
            fotografia=fotografia,
            semblanza=perfil.semblanza,
            linkedin=perfil.linkedin,
            orcid=perfil.orcid,
            correo_alternativo=perfil.correo_alternativo,
            curp=perfil.curp,
            rfc=perfil.rfc,
            fecha_nacimiento=perfil.fecha_nacimiento.isoformat()
            if perfil.fecha_nacimiento
            else None,
            intereses=perfil.intereses or [],
            habilidades=perfil.habilidades or [],
            sexo=perfil.sexo,
            pais_nacimiento=perfil.pais_nacimiento,
            entidad_federativa=perfil.entidad_federativa,
            estado_civil=perfil.estado_civil,
            nacionalidad=perfil.nacionalidad,
            area_conocimiento=perfil.area_conocimiento,
            fecha_creacion=perfil.fecha_creacion.isoformat(),
            fecha_modificacion=perfil.fecha_modificacion.isoformat(),
        )
