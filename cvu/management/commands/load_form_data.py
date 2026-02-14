import json
import os

from django.conf import settings
from django.core.cache import cache
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Carga los archivos json en el directorio forms cargados como diccionario e identificados por su nombre"

    def handle(self, *args, **options):
        forms_dir = settings.FORMS_ROOT
        self.load_forms(forms_dir)

    def load_forms(self, forms_dir):
        for filename in os.listdir(forms_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(forms_dir, filename)
                with open(file_path, "r") as f:
                    form_data = json.load(f)
                    form_name = os.path.splitext(filename)[0]
                    cache.set(form_name, form_data, None)
            if os.path.isdir(filename):
                self.load_forms(os.path.join(forms_dir, filename))
