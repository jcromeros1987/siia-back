from typing import Optional, Iterable
from uuid import UUID

from django.db import transaction

from cvu.DTOs import CatalogoProductoDTO
from cvu.DTOs.producto_investigador_dto import ProductoInvestigadorCheckerDTO
from cvu.models import CatalogoProducto, User, ProductoInvestigador
from cvu.serializers import ProductoInvestigadorRegisterSerializer


class CVURepository:
    def get_catalogo_productos(self) -> Iterable[CatalogoProductoDTO]:
        instances = CatalogoProducto.objects.all()
        return (instance.to_dto() for instance in instances)

    def get_catologo_producto(self, tipo: str) -> Optional[CatalogoProductoDTO]:
        instance = CatalogoProducto.objects.filter(nombre=tipo).first()
        if not instance:
            return None

        return instance.to_dto()

    @transaction.atomic
    def create_producto_investigador(
        self, contenido: dict, tipo: str, investigador_id: str, is_from_file: bool
    ) -> tuple[bool, dict]:
        investigador = User.objects.filter(id=investigador_id).first()
        if not investigador:
            return False, {"message": "Investigador no encontrado."}

        insert_data = {
            "contenido": contenido,
            "tipo": tipo,
            "investigador": investigador,
            "is_from_file": is_from_file,
        }
        serializer = ProductoInvestigadorRegisterSerializer(data=insert_data)

        if not serializer.is_valid():
            return False, serializer.errors

        serializer.save()

        return True, serializer.data

    def get_producto_investigador(
        self, id_producto: UUID, investigador_id: UUID
    ) -> Optional[ProductoInvestigadorCheckerDTO]:
        investigador = User.objects.filter(id=investigador_id).first()
        if not investigador:
            return None

        instance = ProductoInvestigador.objects.filter(
            id=id_producto, investigador=investigador, status=True
        ).first()
        if not instance:
            return None

        return instance.to_checker_dto()

    def update_producto_investigador(
        self,
        id_producto: UUID,
        investigador_id: UUID,
        data: dict,
        eje: str,
        titulo: str,
    ) -> bool:
        instance = ProductoInvestigador.objects.filter(
            id=id_producto, investigador=investigador_id, status=True
        ).first()
        if not instance:
            return False

        instance.eje = eje
        instance.titulo = titulo
        instance.contenido = data
        instance.save()

        return True
