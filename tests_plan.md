# Plan de pruebas manuales – Sistema de Gestión Académica

## Autenticación y roles
- Login con admin, docente y estudiante redirige a su vista correspondiente (dashboard_admin, dashboard_docente, dashboard_estudiante).
- Usuario inactivo: intenta iniciar sesión y debe bloquear con mensaje.

## Gestión de usuarios
- Admin crea usuario desde la vista de usuarios (no existe registro público).
- Activar/desactivar usuario con `usuario_toggle_activo` y verificar acceso.

## Académico – Cursos/Materias/Matrículas
- Crear/editar/eliminar curso y materia (admin). Ver detalle de curso y materia desde sus URLs.
- Docente accede solo a sus cursos/materias; estudiante solo a cursos donde está matriculado.
- Crear matrícula (admin/docente) y verificar unique constraint; estudiante puede ver su matrícula y detalle.

## Calificaciones
- Registrar calificación (docente/admin) con nota dentro de 0–5; validar que notas fuera de rango no pasan.
- Ver calificación como estudiante (solo las propias) y detalle; docente solo de sus materias.
- Trigger de correo en calificación FINAL (revisar que no falle la vista si no hay SMTP real).

## Asistencia
- Registrar asistencia por estudiante/materia/fecha; validar bloqueo de duplicados.
- Docente solo sobre sus materias; estudiante solo ve las propias asistencias.

## Reportes y exportaciones
- Descargar boletín PDF como estudiante propio; admin/docente puede descargar de otros permitidos.
- Descargar acta de curso PDF (admin o docente del curso).
- Exportar Excel de estudiantes por curso, calificaciones (con filtros), asistencias (con rango de fechas).

## Dashboard y buscador
- Dashboard muestra métricas y gráficas sin valores quemados para cada rol.
- Buscador devuelve resultados filtrados según rol (docente solo sus cursos/estudiantes; estudiante solo los suyos).

## Seguridad de datos
- Estudiante no puede acceder a detalle de curso/materia/matrícula/calificación de otros (comprobar HttpResponseForbidden).
- Docente no puede acceder a cursos/materias ajenos; admin accede a todo.

## UX básica
- Mensajes de éxito/error visibles tras operaciones CRUD.
- Navbar cambia según autenticación/rol; opción de salir funciona sin 405.
