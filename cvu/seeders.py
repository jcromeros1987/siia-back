from django_seeding import seeders
from django_seeding.seeder_registry import SeederRegistry

from cvu import models


@SeederRegistry.register
class CatalogoProductosSeeeder(seeders.JSONFileModelSeeder):
    id = "catalogo_productos_seeder"
    priority = 1
    model = models.CatalogoProducto
    json_file_path = "cvu/seeders_data/catalogo_productos.json"
