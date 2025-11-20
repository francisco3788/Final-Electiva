from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import redirect_dashboard

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("academico/", include("academico.urls")),
    path("dashboard/", redirect_dashboard, name="dashboard"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

