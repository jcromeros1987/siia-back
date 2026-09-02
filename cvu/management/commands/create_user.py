from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Creates a new regular user (not superuser)"

    #uv run manage.py create_user admin@planeacion.com.mx "Admin" --first-apellido "Planeacion" --second-apellido "UNAM" --password "12345"
    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="Email address for the user")
        parser.add_argument("name", type=str, help="First name of the user")
        parser.add_argument(
            "--first-apellido", type=str, default=None, help="First surname"
        )
        parser.add_argument(
            "--second-apellido", type=str, default=None, help="Second surname"
        )
        parser.add_argument(
            "--password",
            type=str,
            default=None,
            help="Password for the user (will be prompted if not provided)",
        )

    def handle(self, *args, **options):
        email = options["email"]
        name = options["name"]
        first_apellido = options.get("first_apellido")
        second_apellido = options.get("second_apellido")
        password = options.get("password")

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            raise CommandError(f"User with email '{email}' already exists")

        # Prompt for password if not provided
        if not password:
            from django.core.management import getpass

            password = getpass.getpass("Password: ")
            if not password:
                raise CommandError("Password cannot be empty")

        try:
            user = User.objects.create_user(
                email=email,
                name=name,
                first_apellido=first_apellido,
                second_apellido=second_apellido,
                password=password,
            )
            self.stdout.write(
                self.style.SUCCESS(f"✓ User '{user.email}' created successfully")
            )
        except Exception as e:
            raise CommandError(f"Error creating user: {str(e)}")
