from django_seeding import seeders
from django_seeding.seeder_registry import SeederRegistry

from cvu import models


@SeederRegistry.register
class CatalogoProductosSeeeder(seeders.JSONFileModelSeeder):
    id = "catalogo_productos_seeder"
    priority = 1
    model = models.CatalogoProducto
    json_file_path = "cvu/seeders_data/catalogo_productos.json"


@SeederRegistry.register
class ProyectosInvestigacionSeeder(seeders.Seeder):
    """
    Agrega el tipo de producto proyectosInvestigacion.

    El catálogo original ya quedó aplicado, así que este seeder
    tiene otro id y solo inserta la fila si todavía no existe.
    """

    id = "catalogo_proyectos_investigacion_seeder"
    priority = 2

    def seed(self):
        models.CatalogoProducto.objects.get_or_create(
            nombre="proyectosInvestigacion",
            defaults={"label": "Proyectos de Investigación"},
        )
