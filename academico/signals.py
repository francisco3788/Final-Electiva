from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Calificacion


@receiver(post_save, sender=Calificacion)
def notificar_calificacion(sender, instance, created, **kwargs):
    # Notificar solo calificaciones finales
    if instance.tipo_evaluacion != "FINAL":
        return
    if not instance.estudiante.email:
        return
    subject = "Nueva calificación final registrada"
    message = (
        f"Hola {instance.estudiante.get_full_name() or instance.estudiante.username},\n\n"
        f"Se registró/actualizó tu calificación final en {instance.materia.nombre}.\n"
        f"Nota: {instance.nota}\n"
        f"Fecha: {instance.fecha}\n"
        f"Observaciones: {instance.observaciones or 'N/A'}\n\n"
        "Por favor, revisa la plataforma para más detalles."
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.estudiante.email])
    except Exception:
        # Evitar que errores de email rompan el flujo principal
        pass
