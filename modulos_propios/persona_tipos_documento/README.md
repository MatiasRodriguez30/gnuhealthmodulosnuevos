# Módulo: persona_tipos_documento

Módulo para **GNU Health 5.0** sobre **Tryton 7.0** (Python 3.11).

## Objetivo

Ampliar los tipos de documentos de identidad disponibles en el alta y gestión de personas (`party.party` y pacientes de GNU Health), incorporando documentos de identidad históricos y actuales de uso extendido en Argentina e identificaciones internacionales.

---

## Tipos de Documento Incorporados

El modelo `party.identifier` incorpora a través del método `get_types()` los siguientes tipos adicionales (con etiquetas en español):

| Código (`type`) | Etiqueta en Español | Descripción | Regla de Validación (`check_code`) |
|---|---|---|---|
| `ar_le` | **Libreta de Enrolamiento** | Documento histórico argentino emitido a varones mayores de 18 años. | 6 a 8 dígitos numéricos. Admite puntos o espacios de formato habituales. |
| `ar_lc` | **Libreta Cívica** | Documento histórico argentino emitido a mujeres. | 6 a 8 dígitos numéricos. Admite puntos o espacios de formato habituales. |
| `ar_cuil` | **CUIL** | Código Único de Identificación Laboral (ANSES). | 11 dígitos numéricos con el mismo algoritmo de dígito verificador (módulo 11) que el CUIT. |
| `passport` | **Pasaporte** | Pasaporte nacional o extranjero. | Alfanumérico de 5 a 20 caracteres (letras y dígitos). |
| `ar_ci` | **Cédula de Identidad** | Cédula de identidad de la Policía Federal Argentina o provincial. | Alfanumérico de 5 a 20 caracteres (letras y dígitos). |

### Tipos Preexistentes
Los tipos de documento ya provistos por Tryton continúan plenamente operativos:
- `ar_dni`: Documento Nacional de Identidad (Argentina). **El módulo lo agrega** porque el core solo ofrece los tipos habilitados en Terceros > Configuración y en `bd_desarrollo` no estaba habilitado.
- `ar_cuit`: Código Único de Identificación Tributaria (Argentina). **El módulo lo agrega** por el mismo motivo; su validación sigue siendo la del core (python-stdnum).
- Demás identificadores internacionales soportados por `python-stdnum`.

### Relación con `gnuhealth.person_alternative_identification`
GNU Health provee de forma nativa el modelo `gnuhealth.person_alternative_identification` con el campo `alternative_id_type` (`country_id`, `passport`, `medical_record`, `ghealth_federation`, `other`), diseñado para números de ficha médica y federación de salud. Este módulo **no modifica ni interfiere con dicho modelo**, concentrándose en el estándar de terceros de Tryton (`party.identifier`), el cual se utiliza para los identificadores legales y fiscales de las personas.

---

## Validación y Compatibilidad con python-stdnum

Tryton delega por defecto la validación de identificadores nacionales a la librería `python-stdnum`. Aquellos tipos nuevos no implementados en dicha librería (como LE, LC o CI) no deben causar errores de tipo `AttributeError` o `ImportError`.

Este módulo resuelve la validación mediante el siguiente esquema en `check_code`:
1. **Tipos nuevos propios (`ar_le`, `ar_lc`, `ar_cuil`, `passport`, `ar_ci`)**:
   - Son interceptados y validados con algoritmos de formato específicos.
   - En caso de código inválido, se dispara la excepción estándar `InvalidIdentifierCode` (subclase de `UserError`) con el mensaje traducido `party.msg_invalid_code`.
2. **Tipos preexistentes o de terceros**:
   - Se delegan al método original mediante `super().check_code()`.
   - Se capturan excepciones de módulos ausentes en `python-stdnum` para asegurar la estabilidad del sistema.

---

## Visualización y Búsqueda

Gracias a la extensión dinámica mediante `PoolMeta` en `party.identifier.get_types()`:
- **Formulario de Identificadores**: Los nuevos tipos aparecen automáticamente en el selector desplegable (*dropdown*) del campo `type` en el formulario de identificadores.
- **Lista de Identificadores**: La columna `type` en la tabla de identificadores dentro de la ficha de la persona/paciente muestra las etiquetas traducidas en español.
- **Filtro y Búsqueda**: Las búsquedas avanzadas y filtros por tipo de identificador incluyen las nuevas opciones sin requerir modificaciones en vistas XML.

---

## Carga Rápida del Documento (`documento_tipo` / `documento_numero`)

Para no tener que entrar a la pestaña **Identificadores** al dar de alta una persona, el
formulario de `party.party` incorpora dos campos de carga rápida:

| Campo | Tipo | Descripción |
|---|---|---|
| `documento_tipo` | Selección (`Function`) | Tipo de documento. Las opciones son las mismas que devuelve `party.identifier.get_types()` (incluye DNI, CUIT, LE, LC, CUIL, pasaporte y cédula). |
| `documento_numero` | Texto (`Function`) | Número de documento. |

**Ambos campos son opcionales:** se puede dar de alta una persona sin cargar documento.

### Cómo se guardan

- El dato real **no se guarda en la persona**: se guarda en el **primer `party.identifier`**
  de la persona (el de menor `sequence` y, en caso de empate, el de menor `id`).
- Al leer la persona, los dos campos muestran el `type` y el `code` de ese primer identificador,
  o quedan vacíos si la persona no tiene ninguno.
- Al **crear** o **escribir** la persona con estos campos, el módulo (`party.py`) los extrae
  antes de delegar en el core y los aplica sobre el identificador:
  - Si la persona ya tiene un identificador, se actualizan solo los datos que se cargaron.
  - Si no tiene ninguno, se crea uno nuevo.
- La validación del número la sigue haciendo `party.identifier` (`check_code`), así que un
  código inválido se rechaza con el error habitual del core.

### Regla de carga parcial

Cargar **un solo dato** (tipo o número) en una persona **sin identificador previo** produce el
error `persona_tipos_documento.msg_documento_incompleto`
(«Cargue el tipo y el número de documento juntos.»), porque no tiene sentido crear un
identificador a medias. Si ya existe un identificador, se puede cambiar solo el tipo o solo
el número.

---

## Estructura del Módulo

```text
persona_tipos_documento/
├── __init__.py        # Registro de party.identifier y party.party en el Pool
├── tryton.cfg         # Metadatos del módulo, dependencias (ir, party, health) y xml
├── identifier.py      # Extensión con PoolMeta de party.identifier (get_types y check_code)
├── party.py           # Extensión de party.party con documento_tipo y documento_numero
├── message.xml        # Mensajes de error (msg_documento_incompleto)
├── tests/
│   └── __init__.py    # Pruebas automatizadas completas con ModuleTestCase
└── README.md          # Esta documentación
```

---

## Cómo Activar el Módulo

> ⚠️ **IMPORTANTE:** No ejecutes estos comandos directamente durante el desarrollo. Deben ser ejecutados por el administrador cuando el módulo sea aprobado.

### 1. Mover el módulo a `modulos_propios/` (cuando esté listo)
Desde la raíz del repositorio (`/media/sf_proyecto_equipo` dentro de la VM):
```bash
git mv Mati/persona_tipos_documento modulos_propios/persona_tipos_documento
```

### 2. Enlazar el módulo en la VM (solo la primera vez)
Dentro de la VM:
```bash
~/sync_modulos.sh
```

### 3. Activar / Actualizar en la base de pruebas
Ejecutar `trytond-admin` sobre la base de pruebas `bd_desarrollo`:
```bash
trytond-admin -c /opt/gnuhealth/his-50/etc/trytond.conf -d bd_desarrollo -u persona_tipos_documento --activate-dependencies
```

### 4. Recargar el cliente
- **Cliente Web**: Recargar con `Ctrl + F5` en el navegador.
- **Cliente Tryton Escritorio**: Reconectar la sesión.

---

## Pruebas Unitarias

El módulo incluye un conjunto exhaustivo de pruebas en `tests/__init__.py` utilizando `ModuleTestCase` de `trytond.tests.test_tryton`:
- `test_validador_le_lc_auxiliar`: Prueba unitaria de formato de 6 a 8 dígitos para LE y LC.
- `test_validador_cuil_auxiliar`: Prueba unitaria de longitud (11 dígitos) y algoritmo módulo 11 para CUIL.
- `test_validador_passport_ci_auxiliar`: Prueba unitaria alfanumérica de 5 a 20 caracteres para Pasaporte y Cédula.
- `test_get_types_incluye_nuevos_tipos`: Verifica la presencia de los 5 nuevos tipos y la conservación de DNI y CUIT en `get_types()`.
- `test_le_valida_y_rechaza`: Guarda LE válido y rechaza códigos de longitud menor o con letras.
- `test_lc_valida_y_rechaza`: Guarda LC válida y rechaza códigos inválidos.
- `test_cuil_valida_y_rechaza`: Guarda CUIL con dígito verificador correcto y rechaza códigos erróneos.
- `test_passport_valida_y_rechaza`: Guarda pasaporte válido y rechaza longitudes menores a 5, mayores a 20 o caracteres no alfanuméricos.
- `test_ci_valida_y_rechaza`: Guarda cédula válida y rechaza códigos inválidos.
- `test_dni_sigue_funcionando`: Verifica que DNI continúe validando según el estándar de Tryton.
- `test_cuit_sigue_funcionando`: Verifica que CUIT continúe validando según el estándar de Tryton.
- `test_check_code_directo`: Prueba directa de invocación de `check_code()` sobre instancias del modelo.
- `test_crear_persona_con_documento`: Crea una persona con `documento_tipo` y `documento_numero` y verifica que se genere un `party.identifier` y que al releer la persona vuelvan los mismos valores.
- `test_escribir_solo_tipo_documento`: Escribe solo `documento_tipo` y verifica que cambie el `type` del identificador existente sin crear otro.
- `test_crear_numero_sin_tipo_falla`: Crear con `documento_numero` y sin `documento_tipo` (y sin identificador previo) lanza `UserError`.
- `test_crear_documento_invalido_falla`: Crear con `ar_dni` y un número inválido lo rechaza la validación de `party.identifier`.
- `test_crear_sin_documento_no_crea_identificadores`: Crear una persona sin datos de documento no genera identificadores.

## Verificación en bd_desarrollo (04/11/2026)

Activado en `bd_desarrollo` el 04/11/2026 con `trytond-admin -u ... --activate-dependencies` (estado `activated`). No se tocó `health50`.

Verificado con el motor real de Tryton, en transacciones que se revirtieron (13 casos, todos correctos): cada tipo (`ar_dni`, `ar_cuit`, `ar_le`, `ar_lc`, `ar_cuil`, `passport`, `ar_ci`) acepta un código válido y rechaza uno inválido, y `get_types()` ofrece los siete.

Corrección hecha al activar: `ar_dni` y `ar_cuit` no estaban disponibles (el core solo ofrece los tipos habilitados en Terceros > Configuración); ahora los agrega este módulo.

**No verificado:** las pruebas de `tests/__init__.py` no se corrieron con el runner de Tryton (no hay entorno de pruebas configurado), el formulario no se vio renderizado en el cliente web, y el servidor Tryton en ejecución necesita reinicio (lo hace Matías) para cargar el código Python nuevo.
