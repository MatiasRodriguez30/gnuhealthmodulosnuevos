# Módulo: persona_tipo_sangre

Módulo para **GNU Health 5.0** sobre **Tryton 7.0** (Python 3.11).

## Objetivo y Funcionalidad

Permite registrar el tipo de sangre (grupo sanguíneo y factor Rh) directamente sobre la persona (`party.party`), sin necesidad de acceder a la historia clínica del paciente.

### Campos agregados a `party.party`

1. **`tipo_sangre`** (`fields.Selection`):
   - **Etiqueta**: 'Grupo sanguíneo'
   - **Opciones**: Vacío, `A`, `B`, `AB`, `O`.
   - **Ayuda**: 'Grupo sanguíneo del sistema ABO (A, B, AB, O).'
2. **`factor_rh`** (`fields.Selection`):
   - **Etiqueta**: 'Factor Rh'
   - **Opciones**: Vacío, `+`, `-`.
   - **Ayuda**: 'Factor Rhesus (+ o -).'
3. **`sangre_resumen`** (`fields.Function` de solo lectura):
   - **Etiqueta**: 'Resumen grupo y factor'
   - **Comportamiento**: Muestra una representación legible y compacta del grupo y factor (por ejemplo, `'A +'`, `'O -'`, `'B'`, `'+'`), o `None` si ningún campo está cargado.

---

## Regla de Sincronización Segura con el Paciente

Cuando una persona registrada en `party.party` ya cuenta con un registro clínico asociado en el modelo de paciente (`gnuhealth.patient`):

1. **Copia de campos vacíos**: Al guardar la persona (`create` o `write`), si el paciente asociado tiene `blood_type` o `rh` **vacíos** (`None` o cadena vacía), el sistema le copia automáticamente el valor correspondiente cargado en la persona.
2. **Prioridad del dato clínico (NO PISAR)**: Si el paciente ya cuenta con un valor cargado en `blood_type` o `rh`, dicho dato **NUNCA** se sobreescribe. Se preserva íntegramente la información registrada en el ámbito médico/clínico.
3. **Valores divergentes**: Si la persona y el paciente tienen valores distintos cargados, el módulo **no realiza ninguna modificación** sobre el paciente. El dato clínico preexistente prevalece.
4. **Integridad del modelo**: No se altera la estructura ni la definición original de los campos del paciente en GNU Health (`gnuhealth.patient`).

---

## Vista

El módulo extiende el formulario de personas (`party.party_view_form`) mediante herencia (`inherit` y `xpath`) en `view/party_form.xml`:
- Agrega un bloque `<group>` titulado **"Grupo sanguíneo"** inmediatamente antes del `<notebook>` del formulario de la persona.
- Dispone los campos `tipo_sangre` y `factor_rh` de forma limpia y ordenada, sin modificar ni reordenar el resto de los componentes del formulario base.

---

## Estructura del Módulo

```text
persona_tipo_sangre/
├── __init__.py        # Registro del modelo party.Party en el Pool de Tryton
├── tryton.cfg         # Metadatos del módulo y dependencias (ir, party, health)
├── party.py           # Extensión con PoolMeta de party.party y lógica de sincronización
├── party.xml          # Registro de la vista heredada en ir.ui.view
├── view/
│   └── party_form.xml # Definición XPath del grupo 'Grupo sanguíneo' en el formulario
├── tests/
│   └── __init__.py    # Pruebas unitarias completas (ModuleTestCase)
└── README.md          # Esta documentación
```

---

## Pruebas Unitarias

El módulo incluye un conjunto de pruebas automatizadas en `tests/__init__.py` utilizando `ModuleTestCase` de `trytond.tests.test_tryton`:

- **`test_guardar_y_leer_tipo_sangre_persona`**: Verifica que los campos `tipo_sangre` y `factor_rh` se guarden y lean correctamente en `party.party`, y que `sangre_resumen` devuelva el valor formateado esperado (ej. `'A +'`).
- **`test_sangre_resumen_variantes`**: Evalúa el comportamiento del campo funcional con diferentes combinaciones (grupo y factor, solo grupo, solo factor, y ambos vacíos).
- **`test_sincronizacion_paciente_campos_vacios`**: Valida que al guardar una persona con paciente asociado cuyos campos `blood_type` y `rh` están vacíos, el paciente reciba automáticamente los datos de la persona.
- **`test_sincronizacion_paciente_con_valor_existente_no_se_pisa`**: Comprueba que si el paciente ya poseía un dato clínico previo (ej. `'AB -'`), la modificación en la persona **no** sobreescribe el dato del paciente.
- **`test_sincronizacion_parcial_paciente`**: Verifica que si el paciente posee uno de los campos completo y el otro vacío, únicamente se actualice el campo vacío.
- **`test_persona_sin_paciente_no_falla`**: Comprueba que personas sin registro de paciente asociado se puedan guardar y actualizar sin generar errores.

---

## Cómo Activar el Módulo

> **IMPORTANTE:** No ejecutar estos comandos sin autorización en la base de datos de pruebas.

### 1. Mover el módulo a `modulos_propios/` (cuando esté listo para probar)
Desde la raíz del repositorio (`/media/sf_proyecto_equipo` dentro de la VM):
```bash
git mv Mati/persona_tipo_sangre modulos_propios/persona_tipo_sangre
```

### 2. Enlazar el módulo en la VM (primera vez)
Dentro de la máquina virtual:
```bash
~/sync_modulos.sh
```

### 3. Activar / Actualizar en la base de pruebas
Ejecutar `trytond-admin` sobre la base de pruebas `bd_desarrollo`:
```bash
trytond-admin -c /opt/gnuhealth/his-50/etc/trytond.conf -d bd_desarrollo -u persona_tipo_sangre --activate-dependencies
```

### 4. Recargar el cliente
- **Cliente Web**: Recargar con `Ctrl + F5` en el navegador.
- **Cliente Tryton de escritorio**: Cerrar y reconectar la sesión.
- Si se modificó código Python y no se observan los cambios, reiniciar el servicio del servidor Tryton.

## Verificación en bd_desarrollo (04/11/2026)

Activado en `bd_desarrollo` el 04/11/2026 con `trytond-admin -u ... --activate-dependencies` (estado `activated`). No se tocó `health50`.

Verificado con el motor real de Tryton, en transacciones que se revirtieron:
- Una persona con grupo y factor se guarda (`sangre_resumen` muestra, por ejemplo, `A +`).
- La sincronización llena los campos de un paciente real cuando están vacíos y **no pisa** un dato clínico ya cargado.

Corrección hecha al activar: la primera versión buscaba pacientes con el campo `name`; en GNU Health 5.0 `gnuhealth.patient` se vincula a la persona con `party`, y con `name` fallaba toda creación de persona con grupo sanguíneo (`KeyError`).

**No verificado:** las pruebas de `tests/__init__.py` no se corrieron con el runner de Tryton (no hay entorno de pruebas configurado), el formulario no se vio renderizado en el cliente web, y el servidor Tryton en ejecución necesita reinicio (lo hace Matías) para cargar el código Python nuevo.
