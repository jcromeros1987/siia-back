import uuid
from unittest.mock import Mock, patch

from cvu.DTOs import CatalogoProductoDTO
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
