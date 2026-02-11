import json
import uuid
from io import StringIO
from unittest.mock import Mock, patch

from cvu.DTOs import CatalogoProductoDTO, ProductoInvestigadorCheckerDTO
from cvu.domain.cvu_service import CVUService
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

            result = service.read_cvu(cvu_file=None, investigador_id=investigador_id)

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

            result = service.read_cvu(cvu_file=cvu_file, investigador_id=None)

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
                cvu_file=invalid_cvu_file, investigador_id=investigador_id
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
                mock_repo = Mock()
                mock_repo_class.return_value = mock_repo
                investigador_id = uuid.uuid4()

                # Mock the serializer
                mock_serializer = Mock()
                mock_serializer.data = {"processed": "data"}
                mock_serializer_class.return_value = mock_serializer

                # Mock the repository methods
                mock_repo.delete_productos_investigador.return_value = Result.ok(None)
                mock_repo.insert_productos_investigador.return_value = Result.ok(
                    "Success"
                )

                service = CVUService()
                cvu_data = {"eje": "test", "titulo": "test title"}
                cvu_file = StringIO(json.dumps(cvu_data))

                result = service.read_cvu(
                    cvu_file=cvu_file, investigador_id=investigador_id
                )

                assert isinstance(result, Result)
                assert result.is_ok()
