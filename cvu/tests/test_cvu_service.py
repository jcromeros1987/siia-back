import json
import uuid
from io import StringIO
from unittest.mock import Mock, patch

from cvu.DTOs import (
    CatalogoProductoDTO,
    PerfilUsuarioDTO,
    ProductoInvestigadorCheckerDTO,
)
from cvu.domain.cvu_service import (
    CVUService,
    build_rizoma_cvu,
    producto_para_rizoma,
)
from cvu.serializers.readers.cvu_serializer import ProductoSerializer
from cvu.utils import Result, ErrorCode


class TestCVUService:
    def test_create_new_entry_returns_error_when_tipo_not_found(self):
        """Test that create_new_entry returns error when tipo doesn't exist."""
        # Mock the repository to return NOT_FOUND error
        with patch("cvu.domain.cvu_service.CVURepository") as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            mock_repo.get_catalogo_producto.return_value = Result.err_from(
                ErrorCode.NOT_FOUND, "Tipo de producto no encontrado"
            )

            service = CVUService()
            investigador_id = uuid.uuid4()

            result = service.create_new_entry(
                data={"eje": "test", "titulo": "test title"},
                tipo="NonExistentType",
                investigador_id=investigador_id,
            )

            assert isinstance(result, Result)
            assert result.is_err()
            assert result.get_error().code == ErrorCode.NOT_FOUND

    def test_create_new_entry_returns_error_when_investigador_not_found(self):
        """Test that create_new_entry returns error when investigador doesn't exist."""
        # Mock the repository
        with patch("cvu.domain.cvu_service.CVURepository") as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            mock_dto = CatalogoProductoDTO(nombre="Articulo", label="Artículo")
            mock_repo.get_catalogo_producto.return_value = Result.ok(mock_dto)
            mock_repo.create_producto_investigador.return_value = Result.err_from(
                ErrorCode.NOT_FOUND, "Investigador no encontrado"
            )

            service = CVUService()
            non_existent_uuid = uuid.uuid4()

            result = service.create_new_entry(
                data={"eje": "test", "titulo": "test title"},
                tipo="Articulo",
                investigador_id=non_existent_uuid,
            )

            assert isinstance(result, Result)
            assert result.is_err()
            assert result.get_error().code == ErrorCode.NOT_FOUND

    def test_create_new_entry_success(self):
        """Test that create_new_entry successfully creates a new product entry."""
        # Mock the repository
        with patch("cvu.domain.cvu_service.CVURepository") as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            investigador_id = uuid.uuid4()
            mock_dto = CatalogoProductoDTO(nombre="Articulo", label="Artículo")
            mock_repo.get_catalogo_producto.return_value = Result.ok(mock_dto)
            mock_repo.create_producto_investigador.return_value = Result.ok(
                {
                    "id": uuid.uuid4(),
                    "investigador": investigador_id,
                    "tipo": "Articulo",
                    "titulo": "test_title",
                }
            )

            service = CVUService()
            result = service.create_new_entry(
                data={"eje": "test_eje", "titulo": "test_title"},
                tipo="Articulo",
                investigador_id=investigador_id,
            )

            assert isinstance(result, Result)
            assert result.is_ok()
            data = result.unwrap()
            assert data["investigador"] == investigador_id

    def test_update_entry_returns_error_when_tipo_not_found(self):
        """Test that update_entry returns error when tipo doesn't exist."""
        with patch("cvu.domain.cvu_service.CVURepository") as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            mock_repo.get_catalogo_producto.return_value = Result.err_from(
                ErrorCode.NOT_FOUND, "Tipo de producto no encontrado"
            )

            service = CVUService()
            entry_id = uuid.uuid4()
            investigador_id = uuid.uuid4()

            result = service.update_entry(
                id_entry=entry_id,
                data={"eje": "test", "titulo": "updated title"},
                tipo="NonExistentType",
                investigador_id=investigador_id,
            )

            assert isinstance(result, Result)
            assert result.is_err()
            assert result.get_error().code == ErrorCode.NOT_FOUND

    def test_update_entry_returns_error_when_tipo_mismatch(self):
        """Test that update_entry returns error when product type doesn't match."""
        with patch("cvu.domain.cvu_service.CVURepository") as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            entry_id = uuid.uuid4()
            investigador_id = uuid.uuid4()

            mock_dto = CatalogoProductoDTO(nombre="Articulo", label="Artículo")
            mock_repo.get_catalogo_producto.return_value = Result.ok(mock_dto)

            mock_producto = ProductoInvestigadorCheckerDTO(
                id=entry_id,
                tipo="Libro",  # Different type
                investigador=investigador_id,
            )
            mock_repo.get_producto_investigador.return_value = Result.ok(mock_producto)

            service = CVUService()
            result = service.update_entry(
                id_entry=entry_id,
                data={"eje": "test", "titulo": "updated title"},
                tipo="Articulo",
                investigador_id=investigador_id,
            )

            assert isinstance(result, Result)
            assert result.is_err()
            assert result.get_error().code == ErrorCode.VALIDATION_ERROR

    def test_update_entry_success(self):
        """Test that update_entry successfully updates a product entry."""
        with patch("cvu.domain.cvu_service.CVURepository") as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            entry_id = uuid.uuid4()
            investigador_id = uuid.uuid4()

            mock_catalogo_dto = CatalogoProductoDTO(nombre="Articulo", label="Artículo")
            mock_repo.get_catalogo_producto.return_value = Result.ok(mock_catalogo_dto)

            mock_producto = ProductoInvestigadorCheckerDTO(
                id=entry_id, tipo="Articulo", investigador=investigador_id
            )
            mock_repo.get_producto_investigador.return_value = Result.ok(mock_producto)

            mock_repo.update_producto_investigador.return_value = Result.ok(
                mock_producto
            )

            service = CVUService()
            result = service.update_entry(
                id_entry=entry_id,
                data={"eje": "test_eje", "titulo": "updated title"},
                tipo="Articulo",
                investigador_id=investigador_id,
            )

            assert isinstance(result, Result)
            assert result.is_ok()
            updated_data = result.unwrap()
            assert updated_data.id == entry_id

    def test_read_cvu_returns_error_when_no_file(self):
        """Test that read_cvu returns error when no file is provided."""
        with patch("cvu.domain.cvu_service.CVURepository") as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            service = CVUService()
            investigador_id = uuid.uuid4()

            result = service.read_cvu(
                cvu_file=None,
                investigador_id=investigador_id,
                autenticado_id=uuid.uuid4(),
            )

            assert isinstance(result, Result)
            assert result.is_err()
            assert result.get_error().code == ErrorCode.INVALID_INPUT

    def test_read_cvu_returns_error_when_no_investigador_id(self):
        """Test that read_cvu returns error when no investigador_id is provided."""
        with patch("cvu.domain.cvu_service.CVURepository") as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            service = CVUService()
            cvu_file = StringIO(json.dumps({"test": "data"}))

            result = service.read_cvu(
                cvu_file=cvu_file,
                investigador_id=None,
                autenticado_id=uuid.uuid4(),
            )

            assert isinstance(result, Result)
            assert result.is_err()
            assert result.get_error().code == ErrorCode.INVALID_INPUT

    def test_read_cvu_returns_error_on_invalid_json(self):
        """Test that read_cvu returns error when JSON is invalid."""
        with patch("cvu.domain.cvu_service.CVURepository") as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            service = CVUService()
            investigador_id = uuid.uuid4()
            invalid_cvu_file = StringIO("{invalid json}")

            result = service.read_cvu(
                cvu_file=invalid_cvu_file,
                investigador_id=investigador_id,
                autenticado_id=uuid.uuid4(),
            )

            assert isinstance(result, Result)
            assert result.is_err()
            assert result.get_error().code == ErrorCode.INVALID_INPUT

    def test_read_cvu_success(self):
        """Test that read_cvu successfully processes a valid CVU file."""
        with patch("cvu.domain.cvu_service.CVURepository") as mock_repo_class:
            with patch(
                "cvu.domain.cvu_service.PerfilCompletoSerializer"
            ) as mock_serializer_class:
                with patch(
                    "cvu.domain.cvu_service.PerfilUsuario"
                ) as mock_perfil:
                    mock_repo = Mock()
                    mock_repo_class.return_value = mock_repo
                    investigador_id = uuid.uuid4()
                    mock_perfil.objects.filter.return_value.first.return_value.cvu = (
                        "2082010"
                    )

                    # Mock the serializer
                    mock_serializer = Mock()
                    mock_serializer.data = {"processed": "data"}
                    mock_serializer_class.return_value = mock_serializer

                    # Mock the repository methods
                    mock_repo.delete_productos_investigador.return_value = Result.ok(None)
                    mock_repo.insert_productos_investigador.return_value = Result.ok(
                        "Success"
                    )
                    mock_repo.save_cvu_origen.return_value = Result.ok(
                        "CVU original guardado."
                    )
                    mock_repo.get_catalogo_productos.return_value = Result.ok([])

                    service = CVUService()
                    cvu_data = {
                        "perfil": {"cvu": "2082010"},
                        "eje": "test",
                        "titulo": "test title",
                    }
                    cvu_file = StringIO(json.dumps(cvu_data))

                    result = service.read_cvu(
                        cvu_file=cvu_file,
                        investigador_id=investigador_id,
                        autenticado_id=uuid.uuid4(),
                    )

                    assert isinstance(result, Result)
                    assert result.is_ok()
                    mock_repo.save_cvu_origen.assert_called_once_with(
                        investigador_id,
                        cvu_data,
                    )


class TestRizomaExport:
    def test_producto_para_rizoma_keeps_original_id(self):
        item = producto_para_rizoma(
            {"id": "rizoma-1", "titulo": "Artículo"},
            "otro-id",
        )

        assert item["id"] == "rizoma-1"
        assert item["titulo"] == "Artículo"

    def test_producto_para_rizoma_uses_id_producto_when_missing(self):
        item = producto_para_rizoma(
            {"titulo": "Nuevo"},
            "manual-1",
        )

        assert item["id"] == "manual-1"

    def test_producto_para_rizoma_uses_fallback_when_id_producto_missing(self):
        item = producto_para_rizoma(
            {"titulo": "Manual"},
            None,
            "registro-1",
        )

        assert item["id"] == "registro-1"
        assert item["titulo"] == "Manual"

    def test_build_rizoma_cvu_preserves_envelope_and_replaces_data(self):
        origen = {
            "filtro": "todos",
            "nombreInstituciónReceptora": "UNAM",
            "identificadorInstitucion": {"nombre": "UNAM", "valor": "1"},
            "perfil": {
                "id": "perfil-rizoma",
                "login": "ana.lopez",
                "cvu": "viejo",
                "createdDate": "2020-01-01T00:00:00",
                "principal": {
                    "nombre": "Anterior",
                    "datoExtra": "conservar",
                },
                "formacionContinua": {
                    "cursos": [{"id": "curso-viejo"}],
                    "nota": "conservar",
                },
            },
            "aportaciones": {
                "articulosCientifica": [{"id": "art-viejo", "titulo": "Viejo"}],
            },
        }

        document = build_rizoma_cvu(
            {
                "cvu": "2082010",
                "nivel_academico": "Doctorado",
                "titulo": "Dra.",
                "correo_alternativo": "ana@correo.com",
                "nombre": "Ana",
                "primer_apellido": "López",
                "segundo_apellido": "Ruiz",
                "fotografia": None,
                "semblanza": "Semblanza actual",
                "linkedin": None,
                "orcid": "0000-0001",
                "intereses": ["agua"],
                "habilidades": [],
                "curp": None,
                "rfc": None,
                "fecha_nacimiento": "1980-01-02",
                "sexo": {"id": "2", "nombre": "Mujer"},
                "pais_nacimiento": None,
                "entidad_federativa": None,
                "estado_civil": None,
                "nacionalidad": None,
                "area_conocimiento": {"area": {"nombre": "Biología"}},
            },
            {
                "articulosCientifica": [
                    {"id": "art-nuevo", "titulo": "Nuevo artículo"}
                ],
                "cursos": [
                    {"id": "curso-nuevo", "nombre": "Curso actual"}
                ],
            },
            origen,
        )

        assert document["filtro"] == "todos"
        assert document["nombreInstituciónReceptora"] == "UNAM"
        assert document["identificadorInstitucion"]["valor"] == "1"
        assert document["perfil"]["id"] == "perfil-rizoma"
        assert document["perfil"]["login"] == "ana.lopez"
        assert document["perfil"]["createdDate"] == "2020-01-01T00:00:00"
        assert document["perfil"]["cvu"] == "2082010"
        assert document["perfil"]["nivelAcademico"] == "Doctorado"
        assert document["perfil"]["principal"]["nombre"] == "Ana"
        assert document["perfil"]["principal"]["datoExtra"] == "conservar"
        assert document["perfil"]["principal"]["orcId"] == "0000-0001"
        assert document["perfil"]["principal"]["primerApellido"] == "López"
        assert document["aportaciones"]["articulosCientifica"] == [
            {"id": "art-nuevo", "titulo": "Nuevo artículo"}
        ]
        assert document["aportaciones"]["librosCientifica"] == []
        assert document["perfil"]["formacionContinua"]["cursos"] == [
            {"id": "curso-nuevo", "nombre": "Curso actual"}
        ]
        assert document["perfil"]["formacionContinua"]["nota"] == "conservar"
        assert document["perfil"]["trayectoriaAcademica"] == []
        assert document["perfil"]["idiomaLengua"]["idiomas"] == []

    def test_export_cvu_uses_current_products_and_stored_origin(self):
        investigador_id = uuid.uuid4()
        perfil = PerfilUsuarioDTO(
            id=uuid.uuid4(),
            usuario_id=investigador_id,
            cvu="2082010",
            nivel_academico="Doctorado",
            titulo="Dra.",
            nombre="Ana",
            primer_apellido="López",
            segundo_apellido=None,
            fotografia=None,
            semblanza=None,
            linkedin=None,
            orcid="0000-0001",
            correo_alternativo=None,
            curp=None,
            rfc=None,
            fecha_nacimiento=None,
        )

        producto = Mock()
        producto.contenido = {"titulo": "Artículo editado"}
        producto.id_producto = "art-1"
        producto.tipo.nombre = "articulosCientifica"

        perfil_model = Mock()
        perfil_model.cvu_origen = {
            "filtro": "activos",
            "perfil": {"login": "ana.lopez", "id": "abc"},
        }

        with patch("cvu.domain.cvu_service.CVURepository"):
            with patch(
                "cvu.domain.cvu_service.ProductoInvestigador"
            ) as mock_producto:
                with patch(
                    "cvu.domain.cvu_service.PerfilUsuario"
                ) as mock_perfil:
                    mock_producto.objects.filter.return_value.select_related.return_value.order_by.return_value = [
                        producto
                    ]
                    mock_perfil.objects.filter.return_value.first.return_value = (
                        perfil_model
                    )

                    service = CVUService()
                    service.get_perfil_usuario = Mock(
                        return_value=Result.ok(perfil)
                    )

                    result = service.export_cvu(investigador_id)

        assert result.is_ok()
        document = result.unwrap()
        assert document["filtro"] == "activos"
        assert document["perfil"]["login"] == "ana.lopez"
        assert document["perfil"]["cvu"] == "2082010"
        assert document["perfil"]["principal"]["orcId"] == "0000-0001"
        assert document["aportaciones"]["articulosCientifica"] == [
            {"titulo": "Artículo editado", "id": "art-1"}
        ]
        dumped = json.dumps(document, ensure_ascii=False)
        assert "Artículo editado" in dumped

    def test_export_cvu_assigns_record_id_when_product_has_none(self):
        investigador_id = uuid.uuid4()
        registro_id = uuid.uuid4()
        perfil = PerfilUsuarioDTO(
            id=uuid.uuid4(),
            usuario_id=investigador_id,
            cvu="2082010",
            nivel_academico=None,
            titulo=None,
            nombre="Ana",
            primer_apellido="López",
            segundo_apellido=None,
            fotografia=None,
            semblanza=None,
            linkedin=None,
            orcid=None,
            correo_alternativo=None,
            curp=None,
            rfc=None,
            fecha_nacimiento=None,
        )

        producto = Mock()
        producto.contenido = {"titulo": "Capturado en formulario"}
        producto.id_producto = None
        producto.id = registro_id
        producto.tipo.nombre = "articulosCientifica"

        perfil_model = Mock()
        perfil_model.cvu_origen = None

        with patch("cvu.domain.cvu_service.CVURepository"):
            with patch(
                "cvu.domain.cvu_service.ProductoInvestigador"
            ) as mock_producto:
                with patch(
                    "cvu.domain.cvu_service.PerfilUsuario"
                ) as mock_perfil:
                    mock_producto.objects.filter.return_value.select_related.return_value.order_by.return_value = [
                        producto
                    ]
                    mock_perfil.objects.filter.return_value.first.return_value = (
                        perfil_model
                    )

                    service = CVUService()
                    service.get_perfil_usuario = Mock(
                        return_value=Result.ok(perfil)
                    )

                    result = service.export_cvu(investigador_id)

        assert result.is_ok()
        articulos = result.unwrap()["aportaciones"]["articulosCientifica"]
        assert articulos == [
            {
                "titulo": "Capturado en formulario",
                "id": str(registro_id),
            }
        ]


class TestProductoSerializer:
    def test_assigns_id_when_product_has_none(self):
        producto = {"titulo": "Sin identificador"}

        data = ProductoSerializer(instance=producto).data

        assert data["id"]
        assert producto["id"] == data["id"]
        assert data["contenido"]["id"] == data["id"]

    def test_keeps_existing_id(self):
        producto = {"id": "rizoma-9", "titulo": "Con identificador"}

        data = ProductoSerializer(instance=producto).data

        assert data["id"] == "rizoma-9"
        assert producto["id"] == "rizoma-9"
