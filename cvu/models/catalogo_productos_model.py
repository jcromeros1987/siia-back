import uuid

from django.db import models

from cvu.DTOs import CatalogoProductoDTO


class CatalogoProducto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=255)

    class Meta:
        db_table = "cvu_catalogo_productos"
        verbose_name = "Catalogo Producto"
        verbose_name_plural = "Catalogo Productos"

    def __str__(self):
        return self.nombre

    def to_dto(self):
        return CatalogoProductoDTO(nombre=self.nombre)
