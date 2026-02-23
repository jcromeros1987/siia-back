import json
import os.path
from dataclasses import asdict
from typing import Tuple, Any
from uuid import UUID

from django.conf import settings
from django.core.cache import cache

from cvu.DTOs import ProductoInvestigadorCheckerDTO, PerfilUsuarioDTO
from cvu.logger import logger
from cvu.models import ProductoInvestigador
from cvu.repository import CVURepository
from cvu.serializers import PerfilCompletoSerializer
from cvu.utils import Result, ErrorCode


class CVUService:
    def __init__(self):
        self.cvu_repository = CVURepository()
        self._catalogo_productos = None

    @property
    def catalogo_productos(self):
        if self._catalogo_productos is None:
            self._catalogo_productos = self.cvu_repository.get_catalogo_productos()
        return self._catalogo_productos

    def create_new_entry(
        self, data: dict, tipo: str, investigador_id: UUID
    ) -> Result[dict]:
        """
        Creates a new product entry for a researcher.

        Args:
            data: Product data to store.
            tipo: Product type name.
            investigador_id: Researcher's unique identifier.

        Returns:
            Result containing the created product data on success, or an error on failure.
        """
        return self.cvu_repository.get_catalogo_producto(tipo).and_then(
            lambda catalogo: self.cvu_repository.create_producto_investigador(
                contenido=data,
                tipo=catalogo.nombre,
                investigador_id=investigador_id,
                is_from_file=False,
            )
        )

    def update_entry(
        self, id_entry: UUID, data: dict, tipo: str, investigador_id: UUID
    ) -> Result[ProductoInvestigadorCheckerDTO]:
        """
        Updates an existing product entry for a researcher.

        Args:
            id_entry: Product entry's unique identifier.
            data: Updated product data.
            tipo: Product type name.
            investigador_id: Researcher's unique identifier.

        Returns:
            Result containing the updated product on success, or an error on failure.
        """
        return self.cvu_repository.get_catalogo_producto(tipo).and_then(
            lambda catalogo: self.cvu_repository.get_producto_investigador(
                id_entry, investigador_id
            ).and_then(
                lambda producto: (
                    Result.err_from(
                        ErrorCode.VALIDATION_ERROR,
                        f"Tipo de producto no coincide: {producto.tipo} != {catalogo}",
                    )
                    if producto.tipo != catalogo.nombre
                    else self.cvu_repository.update_producto_investigador(
                        id_entry,
                        investigador_id,
                        data,
                        data.get("eje"),
                        data.get("titulo"),
                    )
                )
            )
        )

    def read_cvu(self, cvu_file: Any, investigador_id: UUID) -> Result[str]:
        """
        Reads and processes a CVU file, deleting old entries and inserting new ones.

        Args:
            cvu_file: The CVU file object to read.
            investigador_id: Researcher's unique identifier.

        Returns:
            Result containing a success message on success, or an error on failure.
        """
        if not cvu_file:
            return Result.err_from(
                ErrorCode.INVALID_INPUT, "No se proporcionó un archivo CVU."
            )
        if not investigador_id:
            return Result.err_from(
                ErrorCode.INVALID_INPUT, "No se proporcionó un ID de investigador."
            )

        logger.info(
            f"Usuario está cargando un CVU para el investigador {investigador_id}."
        )
        try:
            cvu_data = json.load(cvu_file)
        except json.JSONDecodeError as e:
            return Result.err_from(ErrorCode.INVALID_INPUT, str(e))

        serializer = PerfilCompletoSerializer(instance=cvu_data)
        serialized_data = serializer.data
        productos = self._get_productos_investigador(serialized_data)

        # Extract profile data from the serialized CVU data
        perfil_data = self.extract_perfil_from_cvu(serialized_data)
        self.save_perfil_usuario(investigador_id, perfil_data)

        return self.cvu_repository.delete_productos_investigador(
            investigador_id, status=True, is_from_file=True, logic=True
        ).and_then(
            lambda _: self.cvu_repository.insert_productos_investigador(
                productos, investigador_id
            )
        )

    def get_productos_investigador(self, investigador_id: UUID) -> dict:
        productos = {}
        products_types_dtos = self.cvu_repository.get_catalogo_productos().unwrap()

        products_names_dict = {dto.nombre: dto.label for dto in products_types_dtos}
        products_names = [dto.nombre for dto in products_types_dtos]

        for producto_type in products_names:
            productos_instances = self.cvu_repository.get_productos_investigador(
                investigador_id=investigador_id,
                tipo=producto_type,
                status=True,
                check_dto=False,
            ).unwrap_or([])
            productos[producto_type] = {
                "nombre": products_names_dict[producto_type],
                "display_spec": self.get_display_data(producto_type),
                "productos": tuple(
                    asdict(instance_dto) for instance_dto in productos_instances
                ),
            }

        return productos

    def get_form_data(self, product_type: str) -> dict:
        """Analiza el contenido de un producto en formato JSON y devuelve un diccionario con los datos del formulario
        que pueden ser utilizados para llenar los campos de un formulario en una interfaz de usuario."""
        product = ProductoInvestigador.objects.filter(tipo__nombre=product_type).first()
        if not product:
            return {}

        forms_dir = settings.FORMS_ROOT
        if not os.path.exists(forms_dir):
            os.makedirs(forms_dir)

        key = self.get_key_form_spec(product_type)
        if key in cache:
            return cache.get(key)

        form_data, order = self._get_form_data(product.contenido, {})
        cache.set(key, form_data, timeout=None)
        with open(os.path.join(forms_dir, f"form_spec_{product_type}.json"), "w") as f:
            json.dump(form_data, f, indent=4)
        return form_data

    def get_display_data(self, product_type: str) -> dict:
        result = self.cvu_repository.get_catalogo_producto(product_type)
        if result.is_err():
            return {}

        key = self.get_key_display_spec(product_type)
        if key in cache:
            return cache.get(key)

        return {}

    def get_data_display_spec(self, products_type):
        key = self.get_key_form_spec(products_type)
        if key in cache:
            return cache.get(key)

        return {}

    def get_key_form_spec(self, product_type):
        return f"form_spec_{product_type}"

    def get_key_display_spec(self, product_type):
        return f"display_spec_{product_type}"

    def gen_display_data(self):
        for tipo in self.cvu_repository.get_catalogo_productos().unwrap():
            key = self.get_key_display_spec(tipo.nombre)
            # if key in cache:
            #     continue

            muestra = self.cvu_repository.get_muestra_producto_investigador(tipo.nombre)
            if muestra.is_err():
                continue
            display_data, order = self._get_display_data(muestra.unwrap().contenido, {})
            cache.set(key, display_data, timeout=None)
            with open(os.path.join(settings.FORMS_ROOT, f"{key}.json"), "w") as f:
                json.dump(display_data, f, indent=4)

    def _get_display_data(
        self, content: dict, display_data: dict, order: int = 1
    ) -> Tuple[dict, int]:
        current_order = order
        for key, value in content.items():
            match value:
                case str() | int() | bool():
                    display_data[key] = {"label": key, "order": current_order}
                    current_order += 1
                case dict():
                    temp_display, _ = self._get_display_data(value, {})
                    temp_display["label"] = key
                    temp_display["order"] = current_order
                    display_data[key] = temp_display
                    current_order += 1
                case list():
                    if len(value) > 0 and isinstance(value[0], dict):
                        temp_display, _ = self._get_display_data(value[0], {})
                        temp_display["label"] = key
                        temp_display["order"] = current_order
                        temp_display["list"] = True
                        current_order += 1
                        display_data[key] = temp_display

        return display_data, current_order

    def _get_form_data(
        self, content_json: dict, form_data: dict, order: int = 1
    ) -> Tuple[dict, int]:
        current_order = order
        required_fields = ["eje", "titulo"]
        for key, value in content_json.items():
            if key == "id":
                continue

            match value:
                case str():
                    form_data[key] = {
                        "type": "text",
                        "final": True,
                        "order": current_order,
                        "required": key in required_fields,
                        "invalid_feedback": "Este campo es requerido"
                        if key in required_fields
                        else "",
                    }
                    current_order += 1
                case bool():
                    form_data[key] = {
                        "type": "checkbox",
                        "final": True,
                        "order": current_order,
                        "required": key in required_fields,
                        "invalid_feedback": "Este campo es requerido"
                        if key in required_fields
                        else "",
                    }
                    current_order += 1
                case int():
                    form_data[key] = {
                        "type": "number",
                        "final": True,
                        "order": current_order,
                        "required": key in required_fields,
                        "invalid_feedback": "Este campo es requerido"
                        if key in required_fields
                        else "El valor debe ser un número entero",
                    }
                    current_order += 1
                case dict():
                    temp_form, current_order = self._get_form_data(
                        value, {}, current_order
                    )
                    form_data[key] = temp_form
                case list():
                    temp_form, current_order = self._get_form_data(
                        value[0], {}, current_order
                    )
                    temp_form["list"] = True
                    form_data[key] = temp_form

        return form_data, current_order

    def _get_productos_investigador(self, cvu_data: dict) -> dict:
        productos = {}
        tipos = self.catalogo_productos.map_value(
            lambda tipos_cat: [tipo.nombre for tipo in tipos_cat]
        ).unwrap()
        self._get_productos_investigador_aux(cvu_data, tipos, productos)
        return productos

    def _get_productos_investigador_aux(
        self, cvu_data: dict, tipos: list, productos: dict
    ):
        for key, value in cvu_data.items():
            if key in tipos:
                productos[key] = value
            elif isinstance(value, dict):
                self._get_productos_investigador_aux(value, tipos, productos)

    # ==================== Métodos para PerfilUsuario ====================

    def save_perfil_usuario(
        self, investigador_id: UUID, data: dict
    ) -> Result[PerfilUsuarioDTO]:
        """
        Saves or updates the user profile information for a researcher.

        Args:
            investigador_id (UUID): The researcher's unique identifier.
            data (dict): The profile data to save, following the PrincipalSerializer structure.

        Returns:
            Result[PerfilUsuarioDTO]: A Result object containing:
                - On success: A PerfilUsuarioDTO object with the saved profile data.
                - On failure: An error Result with ErrorCode.NOT_FOUND if the researcher doesn't exist,
                  or ErrorCode.VALIDATION_ERROR if the data is invalid.
        """
        logger.info(f"Saving profile for investigador_id: {investigador_id}")
        return self.cvu_repository.create_or_update_perfil_usuario(
            investigador_id, data
        )

    def get_perfil_usuario(self, investigador_id: UUID) -> Result[PerfilUsuarioDTO]:
        """
        Retrieves the user profile information for a researcher.

        Args:
            investigador_id (UUID): The researcher's unique identifier.

        Returns:
            Result[PerfilUsuarioDTO]: A Result object containing:
                - On success: A PerfilUsuarioDTO object with the profile data.
                - On failure: An error Result with ErrorCode.NOT_FOUND if the researcher or profile doesn't exist.
        """
        logger.info(f"Retrieving profile for investigador_id: {investigador_id}")
        return self.cvu_repository.get_perfil_usuario(investigador_id)

    def delete_perfil_usuario(self, investigador_id: UUID) -> Result[str]:
        """
        Deletes the user profile for a researcher.

        Args:
            investigador_id (UUID): The researcher's unique identifier.

        Returns:
            Result[str]: A Result object containing:
                - On success: A success message "Perfil eliminado".
                - On failure: An error Result with ErrorCode.NOT_FOUND if the researcher or profile doesn't exist.
        """
        logger.info(f"Deleting profile for investigador_id: {investigador_id}")
        return self.cvu_repository.delete_perfil_usuario(investigador_id)

    def extract_perfil_from_cvu(self, cvu_data: dict) -> dict:
        """
        Extracts the principal/profile information from a complete CVU data structure.

        Args:
            cvu_data (dict): The complete CVU data structure.

        Returns:
            dict: A dictionary containing the principal profile information.
        """
        perfil_data = cvu_data.get("perfil", {})
        principal_data = perfil_data.get("principal", {})

        return {
            "cvu": perfil_data.get("cvu"),
            "nivel_academico": perfil_data.get("nivelAcademico"),
            "titulo": perfil_data.get("titulo"),
            "nombre": principal_data.get("nombre"),
            "primer_apellido": principal_data.get("primerApellido"),
            "segundo_apellido": principal_data.get("segundoApellido"),
            "fotografia": principal_data.get("fotografia"),
            "semblanza": principal_data.get("semblanza"),
            "linkedin": principal_data.get("linkedin"),
            "orcid": principal_data.get("orcId"),
            "intereses": principal_data.get("intereses", []),
            "habilidades": principal_data.get("habilidades", []),
            "curp": principal_data.get("curp"),
            "rfc": principal_data.get("rfc"),
            "fecha_nacimiento": principal_data.get("fechaNacimiento"),
            "sexo": principal_data.get("sexo"),
            "pais_nacimiento": principal_data.get("paisNacimiento"),
            "entidad_federativa": principal_data.get("entidadFederativa"),
            "estado_civil": principal_data.get("estadoCivil"),
            "nacionalidad": principal_data.get("nacionalidad"),
            "area_conocimiento": principal_data.get("areaConocimiento"),
        }
