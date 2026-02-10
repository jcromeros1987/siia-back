import uuid

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

    @pytest.mark.django_db
    def test_create_producto_investigador_returns_error_when_investigador_not_found(
        self,
    ):
        """Test that create_producto_investigador returns error when investigador doesn't exist."""
        repository = CVURepository()
        non_existent_uuid = uuid.uuid4()
        result = repository.create_producto_investigador(
            contenido={"test": "data"},
            tipo="Articulo",
            investigador_id=non_existent_uuid,
            is_from_file=False,
        )

        assert isinstance(result, Result)
        assert result.is_err()
        assert result.get_error().code == ErrorCode.NOT_FOUND

    @pytest.mark.django_db
    def test_create_producto_investigador_success(self):
        """Test that create_producto_investigador successfully creates a product."""
        from cvu.models import User, CatalogoProducto

        # Create a test investigador
        investigador = User.objects.create(id=uuid.uuid4(), email="test@example.com")
        tipo, _ = CatalogoProducto.objects.get_or_create(nombre="Articulo")

        repository = CVURepository()

        result = repository.create_producto_investigador(
            contenido={"eje": "eje", "titulo": "titulo", "test": "data"},
            tipo=tipo.nombre,
            investigador_id=investigador.id,
            is_from_file=False,
        )

        assert isinstance(result, Result)
        print(result.to_dict())
        assert result.is_ok()
        assert result.unwrap()["investigador"] == investigador.id

    @pytest.mark.django_db
    def test_get_producto_investigador_returns_error_when_investigador_not_found(self):
        """Test that get_producto_investigador returns error when investigador doesn't exist."""
        repository = CVURepository()
        non_existent_uuid = uuid.uuid4()
        product_uuid = uuid.uuid4()

        result = repository.get_producto_investigador(
            id_producto=product_uuid, investigador_id=non_existent_uuid
        )

        assert isinstance(result, Result)
        assert result.is_err()
        assert result.get_error().code == ErrorCode.NOT_FOUND

    @pytest.mark.django_db
    def test_get_producto_investigador_returns_error_when_product_not_found(self):
        """Test that get_producto_investigador returns error when product doesn't exist."""
        from cvu.models import User

        # Create a test investigador
        investigador = User.objects.create(id=uuid.uuid4(), email="test@example.com")
        non_existent_product_uuid = uuid.uuid4()

        repository = CVURepository()
        result = repository.get_producto_investigador(
            id_producto=non_existent_product_uuid, investigador_id=investigador.id
        )

        assert isinstance(result, Result)
        assert result.is_err()
        assert result.get_error().code == ErrorCode.NOT_FOUND

    @pytest.mark.django_db
    def test_get_producto_investigador_success(self):
        """Test that get_producto_investigador successfully retrieves a product."""
        from cvu.models import User, CatalogoProducto, ProductoInvestigador

        # Create test data
        investigador = User.objects.create(id=uuid.uuid4(), email="test@example.com")
        tipo, _ = CatalogoProducto.objects.get_or_create(nombre="Articulo")
        producto = ProductoInvestigador.objects.create(
            titulo="Test Product",
            tipo=tipo,
            investigador=investigador,
            contenido={"test": "data"},
            status=True,
        )

        repository = CVURepository()
        result = repository.get_producto_investigador(
            id_producto=producto.id, investigador_id=investigador.id
        )

        assert isinstance(result, Result)
        assert result.is_ok()
        dto = result.unwrap()
        assert dto.id == producto.id
        assert dto.tipo == "Articulo"
        assert dto.investigador == investigador.id
