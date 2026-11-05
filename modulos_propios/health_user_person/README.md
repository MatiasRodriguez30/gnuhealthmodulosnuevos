# health_user_person

Módulo para GNU Health 5.0 / Tryton 7.0.

## Qué hace

Agrega el campo **Persona** en la ficha del usuario. Permite:

- Buscar y vincular una persona existente (`party.party`).
- Crear una persona nueva usando el botón **“Crear…”** que ya trae el
  Many2One estándar de Tryton (abre el formulario completo de persona).

El vínculo se guarda en `party.internal_user`.

## Qué NO hace

No agrega un formulario propio de alta de persona: se usa el formulario
estándar de GNU Health/Tryton. El intento anterior con un asistente propio
se descartó porque duplicaba esa funcionalidad.

## Activación

```bash
/opt/gnuhealth/his-50/venv/bin/trytond-admin \
  -c /opt/gnuhealth/his-50/etc/trytond.conf \
  -d bd_desarrollo -u health_user_person --activate-dependencies < /dev/null
```

No activar en `health50` sin autorización.

## Revisión y correcciones (2026-11-05)

- La búsqueda por el campo Persona ahora resuelve `= None` (usuarios sin
  persona vinculada) y `!= None` (usuarios con persona).
- `tests/__init__.py` con `ModuleTestCase` y una prueba de vincular, buscar y
  desvincular. No se corrió con el runner de Tryton.
- Verificado con el motor real de Tryton (transacción revertida): vincula,
  busca por id, por nombre, con y sin persona, y desvincula; rechaza lo que no
  es persona y la misma persona para dos usuarios.
