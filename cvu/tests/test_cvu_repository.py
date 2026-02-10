import pytest
from cvu.repository.cvu_repository import CVURepository
from cvu.utils import Result, ErrorCode


class TestCVURepository:
    @pytest.mark.django_db
    def test_get_catalogo_productos_exists(self):
        """Test that get_catalogo_productos method exists in CVURepository."""
        repository = CVURepository()
        assert hasattr(repository, "get_catalogo_productos")
        assert callable(getattr(repository, "get_catalogo_productos"))

    @pytest.mark.django_db
    def test_get_catalogo_productos_returns_result(self):
        """Test that get_catalogo_productos method returns a Result object."""
        repository = CVURepository()
        result = repository.get_catalogo_productos()
        assert isinstance(result, Result)

    @pytest.mark.django_db
    def test_get_catalogo_producto_returns_error_when_tipo_not_found(self):
        """Test that get_catalogo_producto returns an error when tipo is not found."""
        repository = CVURepository()
        result = repository.get_catalogo_producto("non_existent_tipo")

        assert isinstance(result, Result)
        assert result.is_err()
        assert result.get_error().code == ErrorCode.NOT_FOUND
        assert "Tipo de producto no encontrado" in result.get_error().message

    @pytest.mark.django_db
    def test_get_catalogo_producto_returns_success_when_tipo_exists(self):
        """Test that get_catalogo_producto returns success when tipo exists."""
        from cvu.models import CatalogoProducto

        # Create a test product type
        CatalogoProducto.objects.get_or_create(nombre="Articulo")

        repository = CVURepository()
        result = repository.get_catalogo_producto("Articulo")

        assert isinstance(result, Result)
        assert result.is_ok()
        assert result.unwrap().nombre == "Articulo"
