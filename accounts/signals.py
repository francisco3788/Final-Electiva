from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, PerfilDocente, PerfilEstudiante


@receiver(post_save, sender=User)
def crear_perfil(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.role == "DOCENTE":
        PerfilDocente.objects.create(user=instance)
    elif instance.role == "ESTUDIANTE":
        # Provide a placeholder code; admin must update with a unique code
        PerfilEstudiante.objects.create(user=instance, codigo_estudiante=f"AUTO-{instance.id}", programa="Pendiente")
