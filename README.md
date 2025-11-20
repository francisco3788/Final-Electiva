# Sistema de Gestión Académica (Django)

Proyecto universitario completo en Django que implementa autenticación con roles, gestión académica, reportes PDF/Excel y panel con gráficas.

## Tecnologías y versiones sugeridas
- Python 3.10+
- Django 4.2
- SQLite por defecto. Para producción se recomienda PostgreSQL.

## Instalación y ejecución
1. Crear entorno virtual  
   ```bash
   python -m venv venv
   venv\\Scripts\\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```
2. Instalar dependencias  
   ```bash
   pip install -r requirements.txt
   ```
3. Migraciones  
   ```bash
   python manage.py makemigrations accounts academico
   python manage.py migrate
   ```
4. Crear superusuario  
   ```bash
   python manage.py createsuperuser
   ```
5. Arrancar servidor  
   ```bash
   python manage.py runserver
   ```

## Variables de entorno (email y despliegue)
Configura en tu entorno o servicio de despliegue:
```
DJANGO_SECRET_KEY=tu-clave-segura
DJANGO_DEBUG=False  # en producción
DJANGO_ALLOWED_HOSTS=tu-dominio.com

EMAIL_HOST=smtp.tu-proveedor.com
EMAIL_PORT=587
EMAIL_HOST_USER=usuario@correo.com
EMAIL_HOST_PASSWORD=contraseña
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=notificaciones@tu-dominio.com
```

## Cambiar a PostgreSQL
En `gestion_academica/settings.py` sustituye la configuración de `DATABASES` por:
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "nombre_db",
        "USER": "usuario",
        "PASSWORD": "contraseña",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
```

## Estructura de apps y modelos
- **accounts**: Usuario personalizado (`User` con campo `role`), `PerfilDocente`, `PerfilEstudiante`.
- **academico**: `Curso`, `Materia`, `Matricula` (estudiante ↔ curso, con unicidad), `Calificacion`, `Asistencia`.

## Rutas principales
- Autenticación: `/login/`, `/logout/`, `/registrar/` (admin), `/usuarios/`.
- Dashboard: `/dashboard/`.
- Cursos/Materias/Calificaciones/Asistencias: `/academico/...`.
- Buscador global: `/academico/buscar/`.
- Panel de promedios: `/academico/panel-promedios/`.
- Reportes: `/academico/reportes/` (PDF y Excel).

## Despliegue
- Incluye `Procfile` para servicios estilo Render/Railway (`web: gunicorn gestion_academica.wsgi`).
- Ajusta variables de entorno y la base de datos (idealmente PostgreSQL).

## Ajustes recientes
- Registro público deshabilitado: la creación de usuarios es responsabilidad del administrador (vista protegida y/o admin de Django).
- Redirección post-login depende del rol (admin/docente/estudiante) hacia sus dashboards respectivos.
- CRUDs incluyen vistas de detalle para curso, materia, matrícula y calificación.
- Plan de pruebas manuales documentado en `tests_plan.md`.

## Modelos (resumen)
- `User`: username, nombre, email, `role` (ADMIN/DOCENTE/ESTUDIANTE), `is_active`.
- `PerfilDocente`: especialidad, teléfono.
- `PerfilEstudiante`: código_estudiante, programa, fecha_nacimiento.
- `Curso`: nombre, código, periodo_académico, docente_responsable.
- `Materia`: pertenece a curso, código, nombre, intensidad horaria.
- `Matricula`: estudiante ↔ curso (única por combinación).
- `Calificacion`: estudiante, materia, nota (0-5), tipo_evaluación, fecha, observaciones.
- `Asistencia`: estudiante, materia, fecha, estado (presente/ausente/tarde/justificado).

## Notas
- Sistema de mensajes en templates y navbar dinámico según rol.
- Gráficas con Chart.js (por CDN) en dashboard (promedios y asistencia).
- Reportes PDF con ReportLab y Excel con pandas/openpyxl.
- Envío de correo en calificaciones finales (signal en `academico/signals.py`).
