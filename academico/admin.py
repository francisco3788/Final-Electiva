from django.contrib import admin
from .models import Curso, Materia, Matricula, Calificacion, Asistencia


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "periodo_academico", "docente_responsable")
    search_fields = ("codigo", "nombre")
    list_filter = ("periodo_academico",)


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "curso", "intensidad_horaria")
    search_fields = ("codigo", "nombre")
    list_filter = ("curso",)


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "curso", "fecha_matricula")
    search_fields = ("estudiante__username", "curso__nombre")
    list_filter = ("curso",)


@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "materia", "nota", "tipo_evaluacion", "fecha")
    search_fields = ("estudiante__username", "materia__nombre")
    list_filter = ("tipo_evaluacion", "materia")


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "materia", "fecha", "estado")
    search_fields = ("estudiante__username", "materia__nombre")
    list_filter = ("estado", "materia")
