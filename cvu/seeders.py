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


@SeederRegistry.register
class UsuariosPruebaSeeder(seeders.Seeder):
    """
    Crea usuarios de prueba para iniciar sesión.

    Admin puede ya existir en la base. Este seeder tiene su propio id
    y solo inserta cada correo si todavía no está registrado.
    """

    id = "usuarios_prueba_seeder"
    priority = 3

    def seed(self):
        usuarios = [
            {
                "email": "admin@planeacion.com.mx",
                "name": "Admin",
                "first_apellido": "Planeacion",
                "second_apellido": "UNAM",
                "password": "12345",
            },
            {
                "email": "roberto@planeacion.com.mx",
                "name": "Roberto",
                "first_apellido": "Prueba",
                "second_apellido": "CVU",
                "password": "12345",
            },
            {
                "email": "itzel@planeacion.com.mx",
                "name": "Itzel",
                "first_apellido": "Prueba",
                "second_apellido": "CVU",
                "password": "12345",
            },
        ]

        for datos in usuarios:
            if models.User.objects.filter(email=datos["email"]).exists():
                continue
            models.User.objects.create_user(**datos)
