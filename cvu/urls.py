from rest_framework.routers import DefaultRouter

from cvu.views import CVUView

router = DefaultRouter()
router.register(r"", CVUView, basename="cvu")

urlpatterns = router.urls
