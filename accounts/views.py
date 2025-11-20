from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.views import View
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.contrib.auth.forms import SetPasswordForm

from .decorators import role_required
from .forms import CustomUserCreationForm, CustomUserChangeForm, LoginForm
from .models import User


def get_redirect_url_for_role(user):
    if user.role == "ADMIN":
        return reverse("dashboard_admin")
    if user.role == "DOCENTE":
        return reverse("dashboard_docente")
    if user.role == "ESTUDIANTE":
        return reverse("dashboard_estudiante")
    return reverse("dashboard")


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = "accounts/login.html"

    def form_valid(self, form):
        if not form.get_user().is_active:
            messages.error(self.request, "Usuario inactivo, contacte al administrador.")
            return redirect("login")
        login(self.request, form.get_user())
        return redirect(get_redirect_url_for_role(form.get_user()))


class CustomLogoutView(View):
    """
    Permitir logout vía GET y POST para evitar restricciones 405 en navegadores.
    """

    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect("login")

    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect("login")


@login_required
def redirect_dashboard(request):
    # Delegamos la construcción del dashboard a la app académica
    from academico.views import dashboard_view

    return dashboard_view(request)


@login_required
@role_required(["ADMIN"])
def registrar_usuario(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Usuario {user.username} creado correctamente.")
            return redirect("usuarios_lista")
    else:
        form = CustomUserCreationForm()
    return render(request, "accounts/registro.html", {"form": form})


@role_required(["ADMIN"])
def usuarios_lista(request):
    usuarios = User.objects.all().order_by("username")
    return render(request, "accounts/usuarios_lista.html", {"usuarios": usuarios})


@role_required(["ADMIN"])
def usuario_editar(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = CustomUserChangeForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario actualizado.")
            return redirect("usuarios_lista")
    else:
        form = CustomUserChangeForm(instance=usuario)
    return render(request, "accounts/usuario_editar.html", {"form": form, "usuario": usuario})


@role_required(["ADMIN"])
def usuario_toggle_activo(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    usuario.is_active = not usuario.is_active
    usuario.save()
    estado = "activado" if usuario.is_active else "desactivado"
    messages.info(request, f"Usuario {usuario.username} {estado}.")
    return redirect("usuarios_lista")


@role_required(["ADMIN"])
def usuario_reset_password(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    form = SetPasswordForm(usuario, request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Contraseña actualizada para {usuario.username}.")
        return redirect("usuario_editar", pk=pk)
    return render(request, "accounts/usuario_password.html", {"form": form, "usuario": usuario})
