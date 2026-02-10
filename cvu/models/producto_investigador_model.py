import uuid

from django.db import models

from cvu.DTOs import ProductoInvestigadorCheckerDTO, ProductoInvestigadorDTO
from cvu.models import User, CatalogoProducto


class ProductoInvestigador(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_producto = models.CharField(max_length=128, null=True, blank=True)
    eje = models.CharField(max_length=64, null=True, blank=True)
    titulo = models.CharField(max_length=512, null=False, blank=False)
    contenido = models.JSONField(null=True, blank=True)
    tipo = models.ForeignKey(
        CatalogoProducto, on_delete=models.CASCADE, null=False, blank=False
    )
    investigador = models.ForeignKey(
        User, on_delete=models.CASCADE, null=False, blank=False
    )
    is_from_file = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True)

    class Meta:
        db_table = "cvu_productos_investigadores"
        verbose_name = "Producto Investigador"
        verbose_name_plural = "Productos Investigadores"

    def __str__(self):
        return f"{self.titulo} ({self.id_producto})"

    def to_checker_dto(self) -> ProductoInvestigadorCheckerDTO:
        return ProductoInvestigadorCheckerDTO(
            id=self.id,
            tipo=self.tipo.nombre,
            investigador=self.investigador.id,
        )

    def to_dto(self) -> ProductoInvestigadorDTO:
        return ProductoInvestigadorDTO(
            id=self.id,
            tipo=self.tipo.nombre,
            investigador=self.investigador.id,
            contenido=self.contenido,
            eje=self.eje,
            titulo=self.titulo,
            status=self.status,
            is_from_file=self.is_from_file,
        )
