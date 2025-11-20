from django.urls import path
from .views import (
    CustomLoginView,
    CustomLogoutView,
    registrar_usuario,
    usuarios_lista,
    usuario_editar,
    usuario_reset_password,
    usuario_toggle_activo,
)

urlpatterns = [
    path("", CustomLoginView.as_view(), name="home"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
    path("registrar/", registrar_usuario, name="registrar_usuario"),
    path("usuarios/", usuarios_lista, name="usuarios_lista"),
    path("usuarios/<int:pk>/editar/", usuario_editar, name="usuario_editar"),
    path("usuarios/<int:pk>/password/", usuario_reset_password, name="usuario_reset_password"),
    path("usuarios/<int:pk>/toggle/", usuario_toggle_activo, name="usuario_toggle_activo"),
]
