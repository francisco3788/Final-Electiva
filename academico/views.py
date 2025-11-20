import io
import pandas as pd
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors

from accounts.decorators import role_required
from accounts.models import User
from .forms import (
    AsistenciaForm,
    BuscadorForm,
    CalificacionForm,
    CursoForm,
    MateriaForm,
    MatriculaForm,
)
from .models import Asistencia, Calificacion, Curso, Materia, Matricula


def _cursos_por_usuario(user):
    if user.role == "ADMIN":
        return Curso.objects.all()
    if user.role == "DOCENTE":
        return Curso.objects.filter(docente_responsable=user)
    return Curso.objects.filter(matriculas__estudiante=user)


def _materias_por_usuario(user):
    if user.role == "ADMIN":
        return Materia.objects.all()
    if user.role == "DOCENTE":
        return Materia.objects.filter(curso__docente_responsable=user)
    return Materia.objects.filter(curso__matriculas__estudiante=user)


def _estudiantes_del_docente(user):
    if user.role == "DOCENTE":
        return User.objects.filter(matriculas__curso__docente_responsable=user, role="ESTUDIANTE").distinct()
    return User.objects.filter(role="ESTUDIANTE")


@login_required
def dashboard_view(request):
    cursos = _cursos_por_usuario(request.user)
    materias = _materias_por_usuario(request.user)
    estudiantes = _estudiantes_del_docente(request.user)

    total_estudiantes = estudiantes.count()
    total_cursos = cursos.count()
    total_materias = materias.count()

    promedio_materias = (
        materias.annotate(promedio=Avg("calificaciones__nota"))
        .order_by("nombre")
    )
    chart_labels = [m.nombre for m in promedio_materias]
    chart_data = [round(m.promedio or 0, 2) for m in promedio_materias]

    asistencia_qs = Asistencia.objects.filter(materia__in=materias)
    asistencia_por_mes = (
        asistencia_qs.annotate(month=TruncMonth("fecha"))
        .values("month")
        .annotate(total=Count("id"), presentes=Count("id", filter=Q(estado="PRESENTE")))
        .order_by("month")
    )
    asistencia_labels, asistencia_valores = [], []
    for item in asistencia_por_mes:
        asistencia_labels.append(item["month"].strftime("%Y-%m"))
        total = item["total"] or 1
        asistencia_valores.append(round((item["presentes"] / total) * 100, 2))

    contexto = {
        "total_estudiantes": total_estudiantes,
        "total_cursos": total_cursos,
        "total_materias": total_materias,
        "chart_labels": chart_labels,
        "chart_data": chart_data,
        "asistencia_labels": asistencia_labels,
        "asistencia_data": asistencia_valores,
    }
    template = "academico/dashboard_admin.html"
    if request.user.role == "DOCENTE":
        template = "academico/dashboard_docente.html"
    elif request.user.role == "ESTUDIANTE":
        template = "academico/dashboard_estudiante.html"
    return render(request, template, contexto)


@role_required(["ADMIN"])
def dashboard_admin(request):
    return dashboard_view(request)


@role_required(["DOCENTE"])
def dashboard_docente(request):
    return dashboard_view(request)


@role_required(["ESTUDIANTE"])
def dashboard_estudiante(request):
    return dashboard_view(request)


@login_required
def curso_lista(request):
    cursos = _cursos_por_usuario(request.user)
    return render(request, "academico/curso_lista.html", {"cursos": cursos})


@login_required
def curso_detalle(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    if request.user.role == "DOCENTE" and curso.docente_responsable != request.user:
        return HttpResponseForbidden()
    if request.user.role == "ESTUDIANTE" and not Matricula.objects.filter(estudiante=request.user, curso=curso).exists():
        return HttpResponseForbidden()
    return render(request, "academico/curso_detalle.html", {"curso": curso})


@role_required(["ADMIN"])
def curso_crear(request):
    if request.method == "POST":
        form = CursoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Curso creado correctamente.")
            return redirect("curso_lista")
    else:
        form = CursoForm()
    return render(request, "academico/curso_form.html", {"form": form, "titulo": "Crear curso"})


@role_required(["ADMIN"])
def curso_editar(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    form = CursoForm(request.POST or None, instance=curso)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Curso actualizado.")
        return redirect("curso_lista")
    return render(request, "academico/curso_form.html", {"form": form, "titulo": "Editar curso"})


@role_required(["ADMIN"])
def curso_eliminar(request, pk):
    curso = get_object_or_404(Curso, pk=pk)
    curso.delete()
    messages.info(request, "Curso eliminado.")
    return redirect("curso_lista")


@login_required
def materia_lista(request):
    materias = _materias_por_usuario(request.user)
    return render(request, "academico/materia_lista.html", {"materias": materias})


@login_required
def materia_detalle(request, pk):
    materia = get_object_or_404(Materia, pk=pk)
    if request.user.role == "DOCENTE" and materia.curso.docente_responsable != request.user:
        return HttpResponseForbidden()
    if request.user.role == "ESTUDIANTE":
        matriculado = Matricula.objects.filter(estudiante=request.user, curso=materia.curso).exists()
        if not matriculado:
            return HttpResponseForbidden()
    return render(request, "academico/materia_detalle.html", {"materia": materia})


@login_required
def materia_crear(request):
    if request.user.role not in ["ADMIN", "DOCENTE"]:
        return HttpResponseForbidden()
    form = MateriaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        materia = form.save()
        messages.success(request, "Materia creada.")
        return redirect("materia_lista")
    return render(request, "academico/materia_form.html", {"form": form, "titulo": "Crear materia"})


@login_required
def materia_editar(request, pk):
    materia = get_object_or_404(Materia, pk=pk)
    if request.user.role not in ["ADMIN", "DOCENTE"]:
        return HttpResponseForbidden()
    if request.user.role == "DOCENTE" and materia.curso.docente_responsable != request.user:
        return HttpResponseForbidden()
    form = MateriaForm(request.POST or None, instance=materia)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Materia actualizada.")
        return redirect("materia_lista")
    return render(request, "academico/materia_form.html", {"form": form, "titulo": "Editar materia"})


@login_required
def materia_eliminar(request, pk):
    materia = get_object_or_404(Materia, pk=pk)
    if request.user.role not in ["ADMIN", "DOCENTE"]:
        return HttpResponseForbidden()
    if request.user.role == "DOCENTE" and materia.curso.docente_responsable != request.user:
        return HttpResponseForbidden()
    materia.delete()
    messages.info(request, "Materia eliminada.")
    return redirect("materia_lista")


@login_required
def matricula_lista(request):
    if request.user.role == "ESTUDIANTE":
        matriculas = Matricula.objects.filter(estudiante=request.user)
    elif request.user.role == "DOCENTE":
        matriculas = Matricula.objects.filter(curso__docente_responsable=request.user)
    else:
        matriculas = Matricula.objects.all()
    return render(request, "academico/matricula_lista.html", {"matriculas": matriculas})


@login_required
def matricula_detalle(request, pk):
    matricula = get_object_or_404(Matricula, pk=pk)
    if request.user.role == "DOCENTE" and matricula.curso.docente_responsable != request.user:
        return HttpResponseForbidden()
    if request.user.role == "ESTUDIANTE" and matricula.estudiante != request.user:
        return HttpResponseForbidden()
    return render(request, "academico/matricula_detalle.html", {"matricula": matricula})


@login_required
def matricula_crear(request):
    if request.user.role not in ["ADMIN", "DOCENTE"]:
        return HttpResponseForbidden()
    form = MatriculaForm(request.POST or None)
    form.fields["estudiante"].queryset = User.objects.filter(role="ESTUDIANTE", is_active=True)
    if request.user.role == "DOCENTE":
        form.fields["curso"].queryset = Curso.objects.filter(docente_responsable=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Matrícula registrada.")
        return redirect("matricula_lista")
    return render(request, "academico/matricula_form.html", {"form": form, "titulo": "Crear matrícula"})


@login_required
def calificacion_lista(request):
    if request.user.role == "ADMIN":
        calificaciones = Calificacion.objects.select_related("materia", "estudiante")
    elif request.user.role == "DOCENTE":
        calificaciones = Calificacion.objects.filter(materia__curso__docente_responsable=request.user)
    else:
        calificaciones = Calificacion.objects.filter(estudiante=request.user)
    return render(request, "academico/calificacion_lista.html", {"calificaciones": calificaciones})


@login_required
def calificacion_detalle(request, pk):
    calificacion = get_object_or_404(Calificacion, pk=pk)
    if request.user.role == "DOCENTE":
        if calificacion.materia.curso.docente_responsable != request.user and calificacion.creado_por != request.user:
            return HttpResponseForbidden()
    if request.user.role == "ESTUDIANTE" and calificacion.estudiante != request.user:
        return HttpResponseForbidden()
    return render(request, "academico/calificacion_detalle.html", {"calificacion": calificacion})


@login_required
def calificacion_crear(request):
    if request.user.role not in ["ADMIN", "DOCENTE"]:
        return HttpResponseForbidden()
    form = CalificacionForm(request.POST or None)
    estudiantes_qs = _estudiantes_del_docente(request.user)
    form.fields["estudiante"].queryset = estudiantes_qs
    form.fields["materia"].queryset = _materias_por_usuario(request.user)
    if request.method == "POST" and form.is_valid():
        calificacion = form.save(commit=False)
        calificacion.creado_por = request.user if request.user.role == "DOCENTE" else None
        calificacion.save()
        messages.success(request, "Calificación registrada.")
        return redirect("calificacion_lista")
    return render(request, "academico/calificacion_form.html", {"form": form, "titulo": "Crear calificación"})


@login_required
def calificacion_editar(request, pk):
    calificacion = get_object_or_404(Calificacion, pk=pk)
    if request.user.role == "DOCENTE" and calificacion.materia.curso.docente_responsable != request.user:
        return HttpResponseForbidden()
    if request.user.role == "ESTUDIANTE":
        return HttpResponseForbidden()
    form = CalificacionForm(request.POST or None, instance=calificacion)
    form.fields["estudiante"].queryset = _estudiantes_del_docente(request.user)
    form.fields["materia"].queryset = _materias_por_usuario(request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Calificación actualizada.")
        return redirect("calificacion_lista")
    return render(request, "academico/calificacion_form.html", {"form": form, "titulo": "Editar calificación"})


@login_required
def calificacion_eliminar(request, pk):
    calificacion = get_object_or_404(Calificacion, pk=pk)
    if request.user.role == "DOCENTE" and calificacion.materia.curso.docente_responsable != request.user:
        return HttpResponseForbidden()
    if request.user.role == "ESTUDIANTE":
        return HttpResponseForbidden()
    calificacion.delete()
    messages.info(request, "Calificación eliminada.")
    return redirect("calificacion_lista")


@login_required
def asistencia_lista(request):
    if request.user.role == "ADMIN":
        asistencias = Asistencia.objects.select_related("materia", "estudiante")
    elif request.user.role == "DOCENTE":
        asistencias = Asistencia.objects.filter(materia__curso__docente_responsable=request.user)
    else:
        asistencias = Asistencia.objects.filter(estudiante=request.user)
    return render(request, "academico/asistencia_lista.html", {"asistencias": asistencias})


@login_required
def asistencia_crear(request):
    if request.user.role not in ["ADMIN", "DOCENTE"]:
        return HttpResponseForbidden()
    form = AsistenciaForm(request.POST or None)
    form.fields["estudiante"].queryset = _estudiantes_del_docente(request.user)
    form.fields["materia"].queryset = _materias_por_usuario(request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Asistencia registrada.")
        return redirect("asistencia_lista")
    return render(request, "academico/asistencia_form.html", {"form": form, "titulo": "Registrar asistencia"})


@login_required
def asistencia_editar(request, pk):
    asistencia = get_object_or_404(Asistencia, pk=pk)
    if request.user.role == "DOCENTE" and asistencia.materia.curso.docente_responsable != request.user:
        return HttpResponseForbidden()
    if request.user.role == "ESTUDIANTE":
        return HttpResponseForbidden()
    form = AsistenciaForm(request.POST or None, instance=asistencia)
    form.fields["estudiante"].queryset = _estudiantes_del_docente(request.user)
    form.fields["materia"].queryset = _materias_por_usuario(request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Asistencia actualizada.")
        return redirect("asistencia_lista")
    return render(request, "academico/asistencia_form.html", {"form": form, "titulo": "Editar asistencia"})


@login_required
def asistencia_eliminar(request, pk):
    asistencia = get_object_or_404(Asistencia, pk=pk)
    if request.user.role == "DOCENTE" and asistencia.materia.curso.docente_responsable != request.user:
        return HttpResponseForbidden()
    if request.user.role == "ESTUDIANTE":
        return HttpResponseForbidden()
    asistencia.delete()
    messages.info(request, "Asistencia eliminada.")
    return redirect("asistencia_lista")


@login_required
def buscar(request):
    form = BuscadorForm(request.GET or None)
    estudiantes = cursos = None
    if form.is_valid():
        query = form.cleaned_data["query"]
        estudiantes = User.objects.filter(role="ESTUDIANTE").filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(perfil_estudiante__codigo_estudiante__icontains=query)
        )
        cursos = Curso.objects.filter(Q(nombre__icontains=query) | Q(codigo__icontains=query))
        if request.user.role == "DOCENTE":
            cursos = cursos.filter(docente_responsable=request.user)
        if request.user.role == "ESTUDIANTE":
            cursos = cursos.filter(matriculas__estudiante=request.user)
    return render(request, "academico/buscar.html", {"form": form, "estudiantes": estudiantes, "cursos": cursos})


@login_required
def reporte_boletin_pdf(request, estudiante_id=None):
    estudiante = (
        get_object_or_404(User, pk=estudiante_id, role="ESTUDIANTE") if estudiante_id else request.user
    )
    if request.user.role == "ESTUDIANTE" and estudiante != request.user:
        return HttpResponseForbidden()
    if request.user.role == "DOCENTE" and not Matricula.objects.filter(
        estudiante=estudiante, curso__docente_responsable=request.user
    ).exists():
        return HttpResponseForbidden()
    calificaciones = Calificacion.objects.filter(estudiante=estudiante).select_related("materia")
    promedio_global = calificaciones.aggregate(prom=Avg("nota"))["prom"] or 0

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Sistema de Gestión Académica - Boletín", styles["Title"]))
    elements.append(Paragraph(f"Estudiante: {estudiante.get_full_name()}", styles["Normal"]))
    elements.append(Paragraph(f"Código: {getattr(estudiante.perfil_estudiante, 'codigo_estudiante', 'N/A')}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    data = [["Materia", "Tipo", "Nota", "Fecha"]]
    for cal in calificaciones:
        data.append([cal.materia.nombre, cal.get_tipo_evaluacion_display(), float(cal.nota), cal.fecha.strftime("%Y-%m-%d")])
    table = Table(data, hAlign="LEFT")
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.lightblue), ("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
    elements.append(table)
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Promedio general: {round(promedio_global, 2)}", styles["Heading3"]))

    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="boletin_{estudiante.username}.pdf"'
    return response


@login_required
def reporte_acta_curso_pdf(request, curso_id):
    curso = get_object_or_404(Curso, pk=curso_id)
    if request.user.role == "DOCENTE" and curso.docente_responsable != request.user:
        return HttpResponseForbidden()
    if request.user.role == "ESTUDIANTE":
        return HttpResponseForbidden()
    estudiantes = User.objects.filter(matriculas__curso=curso).distinct()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"Acta de curso - {curso.nombre}", styles["Title"]))
    elements.append(Paragraph(f"Periodo: {curso.periodo_academico}", styles["Normal"]))
    elements.append(Spacer(1, 12))
    data = [["Estudiante", "Materia", "Nota", "Tipo"]]
    calificaciones = Calificacion.objects.filter(materia__curso=curso).select_related("estudiante", "materia")
    for cal in calificaciones:
        data.append(
            [
                cal.estudiante.get_full_name(),
                cal.materia.nombre,
                float(cal.nota),
                cal.get_tipo_evaluacion_display(),
            ]
        )
    table = Table(data, hAlign="LEFT")
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey), ("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="acta_{curso.codigo}.pdf"'
    return response


@login_required
def exportar_estudiantes_excel(request, curso_id):
    curso = get_object_or_404(Curso, pk=curso_id)
    if request.user.role == "DOCENTE" and curso.docente_responsable != request.user:
        return HttpResponseForbidden()
    if request.user.role == "ESTUDIANTE" and not Matricula.objects.filter(estudiante=request.user, curso=curso).exists():
        return HttpResponseForbidden()
    estudiantes = User.objects.filter(matriculas__curso=curso, role="ESTUDIANTE")
    datos = [
        {
            "Usuario": est.username,
            "Nombre": est.get_full_name(),
            "Código": getattr(est.perfil_estudiante, "codigo_estudiante", ""),
            "Email": est.email,
        }
        for est in estudiantes
    ]
    df = pd.DataFrame(datos)
    with io.BytesIO() as buffer:
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        response = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    response["Content-Disposition"] = f'attachment; filename="estudiantes_{curso.codigo}.xlsx"'
    return response


@login_required
def exportar_calificaciones_excel(request):
    if request.user.role == "ADMIN":
        calificaciones = Calificacion.objects.all()
    elif request.user.role == "DOCENTE":
        calificaciones = Calificacion.objects.filter(materia__curso__docente_responsable=request.user)
    else:
        calificaciones = Calificacion.objects.filter(estudiante=request.user)
    curso_id = request.GET.get("curso")
    materia_id = request.GET.get("materia")
    if curso_id:
        calificaciones = calificaciones.filter(materia__curso_id=curso_id)
    if materia_id:
        calificaciones = calificaciones.filter(materia_id=materia_id)
    datos = [
        {
            "Estudiante": cal.estudiante.get_full_name(),
            "Materia": cal.materia.nombre,
            "Curso": cal.materia.curso.nombre,
            "Nota": float(cal.nota),
            "Tipo": cal.get_tipo_evaluacion_display(),
            "Fecha": cal.fecha.strftime("%Y-%m-%d"),
        }
        for cal in calificaciones
    ]
    df = pd.DataFrame(datos)
    with io.BytesIO() as buffer:
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        response = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    response["Content-Disposition"] = "attachment; filename=calificaciones.xlsx"
    return response


@login_required
def exportar_asistencias_excel(request):
    desde_str = request.GET.get("desde")
    hasta_str = request.GET.get("hasta")
    if request.user.role == "ADMIN":
        asistencias = Asistencia.objects.all()
    elif request.user.role == "DOCENTE":
        asistencias = Asistencia.objects.filter(materia__curso__docente_responsable=request.user)
    else:
        asistencias = Asistencia.objects.filter(estudiante=request.user)
    if desde_str:
        asistencias = asistencias.filter(fecha__gte=desde_str)
    if hasta_str:
        asistencias = asistencias.filter(fecha__lte=hasta_str)
    datos = [
        {
            "Estudiante": a.estudiante.get_full_name(),
            "Materia": a.materia.nombre,
            "Fecha": a.fecha.strftime("%Y-%m-%d"),
            "Estado": a.get_estado_display(),
        }
        for a in asistencias
    ]
    df = pd.DataFrame(datos)
    with io.BytesIO() as buffer:
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        response = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    response["Content-Disposition"] = "attachment; filename=asistencias.xlsx"
    return response


@login_required
def panel_promedios(request):
    curso_id = request.GET.get("curso")
    periodo = request.GET.get("periodo")
    materias = _materias_por_usuario(request.user)
    if curso_id:
        materias = materias.filter(curso_id=curso_id)
    if periodo:
        materias = materias.filter(curso__periodo_academico__icontains=periodo)
    promedios = materias.annotate(promedio=Avg("calificaciones__nota"))
    cursos = _cursos_por_usuario(request.user)
    return render(
        request,
        "academico/panel_promedios.html",
        {"promedios": promedios, "cursos": cursos, "curso_id": curso_id, "periodo": periodo},
    )


@login_required
def reportes_dashboard(request):
    cursos = _cursos_por_usuario(request.user)
    return render(request, "academico/reportes_dashboard.html", {"cursos": cursos})
