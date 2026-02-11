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

    @pytest.mark.django_db
    def test_get_productos_investigador_returns_error_when_investigador_not_found(self):
        """Test that get_productos_investigador returns error when investigador doesn't exist."""
        repository = CVURepository()
        non_existent_uuid = uuid.uuid4()

        result = repository.get_productos_investigador(
            investigador_id=non_existent_uuid
        )

        assert isinstance(result, Result)
        assert result.is_err()
        assert result.get_error().code == ErrorCode.NOT_FOUND

    @pytest.mark.django_db
    def test_get_productos_investigador_returns_empty_when_no_products(self):
        """Test that get_productos_investigador returns empty iterable when investigador has no products."""
        from cvu.models import User

        # Create a test investigador with no products
        investigador = User.objects.create(id=uuid.uuid4(), email="test@example.com")

        repository = CVURepository()
        result = repository.get_productos_investigador(investigador_id=investigador.id)

        assert isinstance(result, Result)
        assert result.is_ok()
        assert len(result.unwrap()) == 0

    @pytest.mark.django_db
    def test_get_productos_investigador_returns_all_products(self):
        """Test that get_productos_investigador returns all products for an investigador."""
        from cvu.models import User, CatalogoProducto, ProductoInvestigador

        # Create test data
        investigador = User.objects.create(id=uuid.uuid4(), email="test@example.com")
        tipo, _ = CatalogoProducto.objects.get_or_create(nombre="Articulo")

        # Create multiple products
        ProductoInvestigador.objects.create(
            titulo="Product 1",
            tipo=tipo,
            investigador=investigador,
            status=True,
        )
        ProductoInvestigador.objects.create(
            titulo="Product 2",
            tipo=tipo,
            investigador=investigador,
            status=True,
        )

        repository = CVURepository()
        result = repository.get_productos_investigador(investigador_id=investigador.id)

        assert isinstance(result, Result)
        assert result.is_ok()
        assert len(result.unwrap()) == 2

    @pytest.mark.django_db
    def test_get_productos_investigador_filters_by_status(self):
        """Test that get_productos_investigador filters by status correctly."""
        from cvu.models import User, CatalogoProducto, ProductoInvestigador

        # Create test data
        investigador = User.objects.create(id=uuid.uuid4(), email="test@example.com")
        tipo, _ = CatalogoProducto.objects.get_or_create(nombre="Articulo")

        # Create products with different statuses
        ProductoInvestigador.objects.create(
            titulo="Active Product",
            tipo=tipo,
            investigador=investigador,
            status=True,
        )
        ProductoInvestigador.objects.create(
            titulo="Inactive Product",
            tipo=tipo,
            investigador=investigador,
            status=False,
        )

        repository = CVURepository()
        result = repository.get_productos_investigador(
            investigador_id=investigador.id, status=True
        )

        assert isinstance(result, Result)
        assert result.is_ok()
        assert len(result.unwrap()) == 1

    @pytest.mark.django_db
    def test_get_productos_investigador_filters_by_tipo(self):
        """Test that get_productos_investigador filters by tipo correctly."""
        from cvu.models import User, CatalogoProducto, ProductoInvestigador

        # Create test data
        investigador = User.objects.create(id=uuid.uuid4(), email="test@example.com")
        articulo_tipo, _ = CatalogoProducto.objects.get_or_create(nombre="Articulo")
        libro_tipo, _ = CatalogoProducto.objects.get_or_create(nombre="Libro")

        # Create products with different types
        ProductoInvestigador.objects.create(
            titulo="Test Article",
            tipo=articulo_tipo,
            investigador=investigador,
        )
        ProductoInvestigador.objects.create(
            titulo="Test Book",
            tipo=libro_tipo,
            investigador=investigador,
        )

        repository = CVURepository()
        result = repository.get_productos_investigador(
            investigador_id=investigador.id, tipo="Articulo"
        )

        assert isinstance(result, Result)
        assert result.is_ok()
        productos = result.unwrap()
        assert len(productos) == 1
        assert productos[0].tipo == "Articulo"

    @pytest.mark.django_db
    def test_get_productos_investigador_check_dto_true(self):
        """Test that get_productos_investigador returns ProductoInvestigadorCheckerDTO when check_dto=True."""
        from cvu.models import User, CatalogoProducto, ProductoInvestigador
        from cvu.DTOs.producto_investigador_dto import ProductoInvestigadorCheckerDTO

        # Create test data
        investigador = User.objects.create(id=uuid.uuid4(), email="test@example.com")
        tipo, _ = CatalogoProducto.objects.get_or_create(nombre="Articulo")

        ProductoInvestigador.objects.create(
            titulo="Test Product",
            tipo=tipo,
            investigador=investigador,
        )

        repository = CVURepository()
        result = repository.get_productos_investigador(
            investigador_id=investigador.id, check_dto=True
        )

        assert isinstance(result, Result)
        assert result.is_ok()
        productos = result.unwrap()
        assert len(productos) == 1
        assert isinstance(productos[0], ProductoInvestigadorCheckerDTO)

    @pytest.mark.django_db
    def test_get_productos_investigador_check_dto_false(self):
        """Test that get_productos_investigador returns ProductoInvestigadorDTO when check_dto=False."""
        from cvu.models import User, CatalogoProducto, ProductoInvestigador
        from cvu.DTOs.producto_investigador_dto import ProductoInvestigadorDTO

        # Create test data
        investigador = User.objects.create(id=uuid.uuid4(), email="test@example.com")
        tipo, _ = CatalogoProducto.objects.get_or_create(nombre="Articulo")

        ProductoInvestigador.objects.create(
            titulo="Test Product",
            tipo=tipo,
            investigador=investigador,
            contenido={"test": "data"},
            eje="test_eje",
        )

        repository = CVURepository()
        result = repository.get_productos_investigador(
            investigador_id=investigador.id, check_dto=False
        )

        assert isinstance(result, Result)
        assert result.is_ok()
        productos = result.unwrap()
        assert len(productos) == 1
        assert isinstance(productos[0], ProductoInvestigadorDTO)

    @pytest.mark.django_db
    def test_delete_productos_investigador_returns_error_when_investigador_not_found(
        self,
    ):
        """Test that delete_productos_investigador returns error when investigador doesn't exist."""
        repository = CVURepository()
        non_existent_uuid = uuid.uuid4()

        result = repository.delete_productos_investigador(
            investigador_id=non_existent_uuid
        )

        assert isinstance(result, Result)
        assert result.is_err()
        assert result.get_error().code == ErrorCode.NOT_FOUND

    @pytest.mark.django_db
    def test_delete_productos_investigador_soft_delete(self):
        """Test that delete_productos_investigador performs soft delete when logic=True."""
        from cvu.models import User, CatalogoProducto, ProductoInvestigador

        # Create test data
        investigador = User.objects.create(id=uuid.uuid4(), email="test@example.com")
        tipo, _ = CatalogoProducto.objects.get_or_create(nombre="Articulo")
        ProductoInvestigador.objects.create(
            titulo="Product to Delete",
            tipo=tipo,
            investigador=investigador,
            status=True,
        )

        repository = CVURepository()
        result = repository.delete_productos_investigador(
            investigador_id=investigador.id, logic=True
        )

        assert isinstance(result, Result)
        assert result.is_ok()
        # Verify product still exists but with status=False
        producto = ProductoInvestigador.objects.first()
        assert producto is not None
        assert producto.status is False

    @pytest.mark.django_db
    def test_delete_produtos_investigador_hard_delete(self):
        """Test that delete_productos_investigador performs hard delete when logic=False."""
        from cvu.models import User, CatalogoProducto, ProductoInvestigador

        # Create test data
        investigador = User.objects.create(id=uuid.uuid4(), email="test@example.com")
        tipo, _ = CatalogoProducto.objects.get_or_create(nombre="Articulo")
        ProductoInvestigador.objects.create(
            titulo="Product to Delete",
            tipo=tipo,
            investigador=investigador,
            status=True,
        )

        repository = CVURepository()
        result = repository.delete_productos_investigador(
            investigador_id=investigador.id, logic=False
        )

        assert isinstance(result, Result)
        assert result.is_ok()
        # Verify product is deleted
        assert ProductoInvestigador.objects.count() == 0

    @pytest.mark.django_db
    def test_delete_productos_investigador_filters_by_status(self):
        """Test that delete_productos_investigador filters by status."""
        from cvu.models import User, CatalogoProducto, ProductoInvestigador

        # Create test data
        investigador = User.objects.create(id=uuid.uuid4(), email="test@example.com")
        tipo, _ = CatalogoProducto.objects.get_or_create(nombre="Articulo")
        ProductoInvestigador.objects.create(
            titulo="Active Product",
            tipo=tipo,
            investigador=investigador,
            status=True,
        )
        ProductoInvestigador.objects.create(
            titulo="Inactive Product",
            tipo=tipo,
            investigador=investigador,
            status=False,
        )

        repository = CVURepository()
        result = repository.delete_productos_investigador(
            investigador_id=investigador.id, status=True, logic=False
        )

        assert isinstance(result, Result)
        assert result.is_ok()
        # Verify only active product was deleted
        assert ProductoInvestigador.objects.count() == 1
        assert ProductoInvestigador.objects.first().status is False

    @pytest.mark.django_db
    def test_update_producto_investigador_returns_error_when_product_not_found(self):
        """Test that update_producto_investigador returns error when product doesn't exist."""
        from cvu.models import User

        investigador = User.objects.create(id=uuid.uuid4(), email="test@example.com")
        non_existent_product_uuid = uuid.uuid4()

        repository = CVURepository()
        result = repository.update_producto_investigador(
            id_producto=non_existent_product_uuid,
            investigador_id=investigador.id,
            data={"test": "data"},
            eje="eje",
            titulo="New Title",
        )

        assert isinstance(result, Result)
        assert result.is_err()
        assert result.get_error().code == ErrorCode.NOT_FOUND

    @pytest.mark.django_db
    def test_update_producto_investigador_success(self):
        """Test that update_producto_investigador successfully updates a product."""
        from cvu.models import User, CatalogoProducto, ProductoInvestigador

        # Create test data
        investigador = User.objects.create(id=uuid.uuid4(), email="test@example.com")
        tipo, _ = CatalogoProducto.objects.get_or_create(nombre="Articulo")
        producto = ProductoInvestigador.objects.create(
            titulo="Original Title",
            eje="original_eje",
            tipo=tipo,
            investigador=investigador,
            contenido={"original": "data"},
            status=True,
        )

        repository = CVURepository()
        result = repository.update_producto_investigador(
            id_producto=producto.id,
            investigador_id=investigador.id,
            data={"updated": "data"},
            eje="new_eje",
            titulo="New Title",
        )

        assert isinstance(result, Result)
        assert result.is_ok()
        dto = result.unwrap()
        assert dto.id == producto.id

        # Verify product was updated in database
        updated_producto = ProductoInvestigador.objects.get(id=producto.id)
        assert updated_producto.titulo == "New Title"
        assert updated_producto.eje == "new_eje"
        assert updated_producto.contenido == {"updated": "data"}

    @pytest.mark.django_db
    def test_update_producto_investigador_ignores_inactive_products(self):
        """Test that update_producto_investigador ignores products with status=False."""
        from cvu.models import User, CatalogoProducto, ProductoInvestigador

        # Create test data
        investigador = User.objects.create(id=uuid.uuid4(), email="test@example.com")
        tipo, _ = CatalogoProducto.objects.get_or_create(nombre="Articulo")
        producto = ProductoInvestigador.objects.create(
            titulo="Inactive Product",
            tipo=tipo,
            investigador=investigador,
            status=False,
        )

        repository = CVURepository()
        result = repository.update_producto_investigador(
            id_producto=producto.id,
            investigador_id=investigador.id,
            data={"test": "data"},
            eje="eje",
            titulo="Updated Title",
        )

        assert isinstance(result, Result)
        assert result.is_err()
        assert result.get_error().code == ErrorCode.NOT_FOUND

    @pytest.mark.django_db
    def test_insert_productos_investigador_returns_error_when_investigador_not_found(
        self,
    ):
        """Test that insert_productos_investigador returns error when investigador doesn't exist."""
        repository = CVURepository()
        non_existent_uuid = uuid.uuid4()

        result = repository.insert_productos_investigador(
            productos={"Articulo": []}, investigador_id=non_existent_uuid
        )

        assert isinstance(result, Result)
        assert result.is_err()
        assert result.get_error().code == ErrorCode.NOT_FOUND

    @pytest.mark.django_db
    def test_insert_productos_investigador_success(self):
        """Test that insert_productos_investigador successfully inserts products."""
        from cvu.models import User, CatalogoProducto, ProductoInvestigador

        # Create test data
        investigador = User.objects.create(id=uuid.uuid4(), email="test@example.com")
        CatalogoProducto.objects.get_or_create(nombre="Articulo")

        repository = CVURepository()

        productos = {
            "Articulo": [
                {
                    "id": "prod_1",
                    "eje": "eje_1",
                    "titulo": "Producto 1",
                    "contenido": {"data": "value1"},
                },
                {
                    "id": "prod_2",
                    "eje": "eje_2",
                    "titulo": "Producto 2",
                    "contenido": {"data": "value2"},
                },
            ]
        }

        result = repository.insert_productos_investigador(
            productos=productos, investigador_id=investigador.id
        )

        assert isinstance(result, Result)
        assert result.is_ok()

        # Verify products were created
        created_productos = ProductoInvestigador.objects.filter(
            investigador=investigador
        )
        assert created_productos.count() == 2

    @pytest.mark.django_db
    def test_insert_productos_investigador_empty_list(self):
        """Test that insert_productos_investigador handles empty product list."""
        from cvu.models import User, CatalogoProducto

        # Create test data
        investigador = User.objects.create(id=uuid.uuid4(), email="test@example.com")
        CatalogoProducto.objects.get_or_create(nombre="Articulo")

        repository = CVURepository()

        result = repository.insert_productos_investigador(
            productos={"Articulo": []}, investigador_id=investigador.id
        )

        assert isinstance(result, Result)
        assert result.is_ok()
