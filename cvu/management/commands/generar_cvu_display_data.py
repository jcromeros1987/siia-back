import os.path

from django.conf import settings
from django.core.management import BaseCommand

from cvu.domain import CVUService


class Command(BaseCommand):
    help = "Genera los archivos json con información acerca de cómo mostrar los datos del cvu"
    cvu_service = CVUService()

    def handle(self, *args, **options):
        if not os.path.exists(settings.FORMS_ROOT):
            os.makedirs(settings.FORMS_ROOT)
        self.cvu_service.gen_display_data()
