from typing import Iterable
from uuid import UUID

from django.db import transaction
from django.db.models import QuerySet

from cvu.DTOs import CatalogoProductoDTO
from cvu.DTOs.producto_investigador_dto import ProductoInvestigadorCheckerDTO
from cvu.models import CatalogoProducto, User, ProductoInvestigador
from cvu.serializers import ProductoInvestigadorRegisterSerializer
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
        investigador = User.objects.filter(id=investigador_id).first()
        if not investigador:
            return Result.err_from(ErrorCode.NOT_FOUND, "Investigador no encontrado")

        instance = ProductoInvestigador.objects.filter(
            id=id_producto, investigador=investigador, status=True
        ).first()
        if not instance:
            return Result.err_from(ErrorCode.NOT_FOUND, "Investigador no encontrado")

        return Result.ok(instance.to_checker_dto())

    def get_productos_investigador(
        self, investigador_id: UUID, status: bool = None, is_from_file: bool = None
    ) -> Result[Iterable[ProductoInvestigadorCheckerDTO]]:
        args = {}
        if status is not None:
            args["status"] = status
        if is_from_file is not None:
            args["is_from_file"] = is_from_file

        return self._get_productos_investigador(investigador_id, **args).map_value(
            lambda productos: tuple(producto.to_checker_dto() for producto in productos)
        )

    @transaction.atomic
    def delete_productos_investigador(
        self,
        investigador_id: UUID,
        status: bool = None,
        is_from_file: bool = None,
        logic: bool = False,
    ) -> Result[str]:
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
