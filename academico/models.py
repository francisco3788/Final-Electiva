from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from accounts.models import User


class Curso(models.Model):
    nombre = models.CharField(max_length=120)
    codigo = models.CharField(max_length=20, unique=True)
    periodo_academico = models.CharField(max_length=50)
    docente_responsable = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="cursos_asignados", limit_choices_to={"role": "DOCENTE"}
    )

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Materia(models.Model):
    nombre = models.CharField(max_length=120)
    codigo = models.CharField(max_length=20, unique=True)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="materias")
    intensidad_horaria = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(20)])

    def __str__(self):
        return f"{self.nombre} ({self.curso.codigo})"


class Matricula(models.Model):
    estudiante = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="matriculas", limit_choices_to={"role": "ESTUDIANTE"}
    )
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="matriculas")
    fecha_matricula = models.DateField(default=timezone.now)

    class Meta:
        unique_together = ("estudiante", "curso")

    def __str__(self):
        return f"{self.estudiante} -> {self.curso}"


class Calificacion(models.Model):
    TIPO_EVALUACION = (
        ("PARCIAL", "Parcial"),
        ("FINAL", "Final"),
        ("TAREA", "Tarea"),
        ("QUIZ", "Quiz"),
    )
    estudiante = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="calificaciones", limit_choices_to={"role": "ESTUDIANTE"}
    )
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name="calificaciones")
    nota = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    tipo_evaluacion = models.CharField(max_length=20, choices=TIPO_EVALUACION)
    fecha = models.DateField(default=timezone.now)
    observaciones = models.TextField(blank=True)
    creado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="calificaciones_creadas", limit_choices_to={"role": "DOCENTE"}
    )

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.estudiante} - {self.materia} ({self.nota})"


class Asistencia(models.Model):
    ESTADOS = (
        ("PRESENTE", "Presente"),
        ("AUSENTE", "Ausente"),
        ("TARDE", "Tarde"),
        ("JUSTIFICADO", "Justificado"),
    )
    estudiante = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="asistencias", limit_choices_to={"role": "ESTUDIANTE"}
    )
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name="asistencias")
    fecha = models.DateField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADOS)
    observaciones = models.TextField(blank=True)

    class Meta:
        unique_together = ("estudiante", "materia", "fecha")
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.estudiante} - {self.materia} ({self.estado})"
