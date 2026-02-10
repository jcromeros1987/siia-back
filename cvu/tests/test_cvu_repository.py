import pytest
from cvu.repository.cvu_repository import CVURepository
from cvu.utils import Result


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
