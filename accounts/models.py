from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ("ADMIN", "Administrador"),
        ("DOCENTE", "Docente"),
        ("ESTUDIANTE", "Estudiante"),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="ESTUDIANTE")

    def is_admin(self):
        return self.role == "ADMIN"

    def is_docente(self):
        return self.role == "DOCENTE"

    def is_estudiante(self):
        return self.role == "ESTUDIANTE"

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"


class PerfilDocente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil_docente")
    especialidad = models.CharField(max_length=120, blank=True)
    telefono = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Perfil docente {self.user.get_full_name()}"


class PerfilEstudiante(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil_estudiante")
    codigo_estudiante = models.CharField(max_length=20, unique=True)
    programa = models.CharField(max_length=120)
    fecha_nacimiento = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.codigo_estudiante} - {self.user.get_full_name()}"
