from django import forms
from django.core.exceptions import ValidationError
from .models import Curso, Materia, Matricula, Calificacion, Asistencia


class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ["nombre", "codigo", "periodo_academico", "docente_responsable"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "codigo": forms.TextInput(attrs={"class": "form-control"}),
            "periodo_academico": forms.TextInput(attrs={"class": "form-control"}),
            "docente_responsable": forms.Select(attrs={"class": "form-select"}),
        }


class MateriaForm(forms.ModelForm):
    class Meta:
        model = Materia
        fields = ["nombre", "codigo", "curso", "intensidad_horaria"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "codigo": forms.TextInput(attrs={"class": "form-control"}),
            "curso": forms.Select(attrs={"class": "form-select"}),
            "intensidad_horaria": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 20}),
        }


class MatriculaForm(forms.ModelForm):
    class Meta:
        model = Matricula
        fields = ["estudiante", "curso", "fecha_matricula"]
        widgets = {
            "estudiante": forms.Select(attrs={"class": "form-select"}),
            "curso": forms.Select(attrs={"class": "form-select"}),
            "fecha_matricula": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        estudiante = cleaned.get("estudiante")
        curso = cleaned.get("curso")
        if estudiante and curso and Matricula.objects.filter(estudiante=estudiante, curso=curso).exclude(
            pk=self.instance.pk
        ).exists():
            raise ValidationError("El estudiante ya está matriculado en este curso.")
        return cleaned


class CalificacionForm(forms.ModelForm):
    class Meta:
        model = Calificacion
        fields = ["estudiante", "materia", "nota", "tipo_evaluacion", "fecha", "observaciones"]
        widgets = {
            "estudiante": forms.Select(attrs={"class": "form-select"}),
            "materia": forms.Select(attrs={"class": "form-select"}),
            "nota": forms.NumberInput(attrs={"class": "form-control", "step": "0.1", "min": 0, "max": 5}),
            "tipo_evaluacion": forms.Select(attrs={"class": "form-select"}),
            "fecha": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def clean_nota(self):
        nota = self.cleaned_data["nota"]
        if nota < 0 or nota > 5:
            raise ValidationError("La nota debe estar entre 0.0 y 5.0.")
        return nota


class AsistenciaForm(forms.ModelForm):
    class Meta:
        model = Asistencia
        fields = ["estudiante", "materia", "fecha", "estado", "observaciones"]
        widgets = {
            "estudiante": forms.Select(attrs={"class": "form-select"}),
            "materia": forms.Select(attrs={"class": "form-select"}),
            "fecha": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "estado": forms.Select(attrs={"class": "form-select"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def clean(self):
        cleaned = super().clean()
        est = cleaned.get("estudiante")
        mat = cleaned.get("materia")
        fecha = cleaned.get("fecha")
        if est and mat and fecha and Asistencia.objects.filter(estudiante=est, materia=mat, fecha=fecha).exclude(
            pk=self.instance.pk
        ).exists():
            raise ValidationError("Ya existe una asistencia para este estudiante en esa fecha y materia.")
        return cleaned


class BuscadorForm(forms.Form):
    query = forms.CharField(
        label="Buscar por estudiante o curso",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre, código o documento"}),
    )
