# Módulo: persona_datos_obligatorios

Módulo para **GNU Health 5.0** sobre **Tryton 7.0** (Python 3.11).

## Objetivo y Funcionalidad

Garantiza que al dar de alta o modificar una persona (`party.party` con `is_person=True`), sea **obligatorio** registrar los siguientes datos:
1. **Nombre** (`name`)
2. **Apellido** (`lastname`)
3. **Email** (al menos un registro en `party.contact_mechanism` con tipo `email` y valor no vacío)
4. **Teléfono** (al menos un registro en `party.contact_mechanism` con tipo `phone` o `mobile` y valor no vacío)
5. **Domicilio** (al menos una dirección en `party.address` con calle `street` no vacía)

### Campos de Carga Rápida
Dado que en Tryton los emails y teléfonos se modelan como mecanismos de contacto (`party.contact_mechanism`) y los domicilios como direcciones (`party.address`), este módulo agrega cuatro campos funcionales (`fields.Function`) en `party.party` para simplificar la carga directa:
- `email_principal` (Char): lee o escribe el primer contacto de tipo `email`.
- `telefono_principal` (Char): lee o escribe el primer contacto de tipo `phone` o `mobile`.
- `domicilio_calle` (Text): lee o escribe la calle (`street`) de la primera dirección.
- `domicilio_ciudad` (Char): lee o escribe la ciudad (`city`) de la primera dirección.

### Alcance de la Validación
- **Personas**: La validación aplica cuando `is_person = True` y `is_institution = False`, **solo al crear** el registro. Las personas ya existentes no se revalidan al editarlas.
- **Instituciones y Empresas**: **No aplica** a instituciones (`is_institution = True`) ni a terceros que no sean personas (`is_person = False`). Dichos registros se pueden crear y editar sin requerir estos campos.
- **Mensajes de error**: En caso de omisión, se emiten errores claros en español mediante excepciones `UserError` definidas en `message.xml`.

---

## Decisión de diseño: se exige solo al crear

Los datos obligatorios se validan únicamente al **crear** una persona (`create`). Editar una persona ya existente no vuelve a exigirlos, de modo que los registros anteriores a este módulo (por ejemplo, personas de demostración sin email) se pueden seguir modificando sin completar esos datos.

Límite conocido: si un tercero se crea sin ser persona y después se marca `is_person` mediante una edición, esa edición no dispara la validación.

---

## Estructura del Módulo

```text
persona_datos_obligatorios/
├── __init__.py        # Registro del modelo en el Pool de Tryton
├── tryton.cfg         # Metadatos del módulo y dependencias (ir, party, health)
├── party.py           # Extensión con PoolMeta de party.party (campos rápidos y validación)
├── party.xml          # Registro de herencia de vista en ir.ui.view
├── message.xml        # Definición de mensajes de error en ir.message
├── view/
│   └── party_form.xml # Herencia de vista agregando grupo de datos obligatorios
├── tests/
│   └── __init__.py    # Pruebas unitarias automatizadas (ModuleTestCase)
└── README.md          # Esta documentación
```

---

## Cómo Activar el Módulo

> **Nota:** No ejecutar estos comandos si no se tiene autorización para actualizar la base de datos de pruebas.

### 1. Pasar el módulo a `modulos_propios/` (cuando esté listo)
Desde la raíz del repositorio (`/media/sf_proyecto_equipo` dentro de la VM):
```bash
git mv Mati/persona_datos_obligatorios modulos_propios/persona_datos_obligatorios
```

### 2. Enlazar el módulo en la VM (solo la primera vez)
Dentro de la VM:
```bash
~/sync_modulos.sh
```

### 3. Activar / Actualizar en la base de pruebas
Ejecutar `trytond-admin` sobre la base de pruebas `bd_desarrollo`:
```bash
trytond-admin -c /opt/gnuhealth/his-50/etc/trytond.conf -d bd_desarrollo -u persona_datos_obligatorios --activate-dependencies
```

### 4. Recargar el cliente
- **Web**: Recargar con `Ctrl + F5` en el navegador.
- **Cliente Tryton de escritorio**: Reconectar la sesión.
- Si se modificó código Python y no se observan los cambios, reiniciar el servicio de Tryton.

---

## Pruebas Unitarias

El módulo incluye un conjunto completo de pruebas en `tests/__init__.py` utilizando `ModuleTestCase` de `trytond.tests.test_tryton`:
- `test_persona_sin_email_falla`: Verifica que una persona sin email genere `UserError`.
- `test_persona_completa_guarda`: Verifica que una persona con todos los datos se cree correctamente y persista tanto los campos rápidos como los mecanismos de contacto y direcciones asociados.
- `test_institucion_no_afectada`: Verifica que una institución sanitaria pueda crearse sin requerir estos datos.
- `test_persona_sin_telefono_falla`: Verifica que la omisión de teléfono o móvil genere `UserError`.
- `test_persona_sin_domicilio_falla`: Verifica que la omisión de calle genere `UserError`.
- `test_persona_sin_apellido_falla`: Verifica que la omisión de apellido genere `UserError`.
- `test_tercero_no_persona_no_afectado`: Verifica que empresas o terceros no persona se puedan crear normalmente.

## Verificación en bd_desarrollo (04/11/2026)

Activado en `bd_desarrollo` el 04/11/2026 con `trytond-admin -u ... --activate-dependencies` (estado `activated`). No se tocó `health50`.

Verificado con el motor real de Tryton, en transacciones que se revirtieron (sin commit):
- Crear una persona sin email, sin teléfono, sin apellido o sin domicilio se rechaza con el mensaje en español correspondiente.
- Una persona completa se guarda; los campos rápidos generan el contact mechanism de email, el de teléfono y la dirección.
- Una institución se crea sin esos datos.
- Editar una persona ya existente sin datos no exige nada.

Nota para probar por código: GNU Health exige además `gender`, `fed_country` y el contexto de empresa (`company`) al crear personas; el cliente web los aporta solo.

**No verificado:** las pruebas de `tests/__init__.py` no se corrieron con el runner de Tryton (no hay entorno de pruebas configurado), el formulario no se vio renderizado en el cliente web, y el servidor Tryton en ejecución necesita reinicio (lo hace Matías) para cargar el código Python nuevo.
