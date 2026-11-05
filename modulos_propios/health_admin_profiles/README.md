# Módulo: health_admin_profiles

Módulo para **GNU Health 5.0** sobre **Tryton 7.0** (Python 3.11).

Ubicación del módulo: `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/`

---

## 1. Qué hace el módulo

En GNU Health estándar, la gestión de permisos exige tildar manualmente casillas entre más de 40 grupos de seguridad (`res.group`), lo que resulta propenso a errores y desalineaciones de roles. Asimismo, la especialidad de un profesional de la salud (`gnuhealth.specialty`) funciona únicamente como un dato informativo y no otorga ni revoca permisos operativos.

El módulo `health_admin_profiles` soluciona esta problemática bajo la premisa:  
**Permisos finales = Perfil de Puesto + Área de Especialidad + Grupos Extras Manuales**.

El módulo introduce:
1. **Perfiles de puesto (`gnuhealth.admin.profile`)**: Agrupación predefinida de permisos (`res.group`) según la función organizativa del usuario (médico, enfermero, recepcionista, personal de laboratorio, etc.). Al asignar un perfil a un usuario (`res.user`), el sistema actualiza automáticamente su pertenencia a grupos. Incluye un asistente ("Aplicar a usuarios") para sincronizar cambios de grupos de manera masiva a todos los usuarios asignados a un perfil.
2. **Áreas de especialidad (`gnuhealth.specialty.area`)**: Estructura clasificatoria que agrupa las 74 especialidades médicas del sistema en 11 áreas funcionales (Atención Primaria, Pediatría, Cirugía, Imágenes, etc.), dotando a cada área de grupos de permisos por defecto.
3. **Botón en la ficha del profesional (`gnuhealth.healthprofessional`)**: Botón *"Aplicar permisos de la especialidad"* que ejecuta un asistente interactivo (`gnuhealth.specialty.apply`). En lugar de una asignación automática invisible, permite a un administrador revisar e incorporar explícitamente al usuario interno del profesional los permisos propios de las áreas de sus especialidades.
4. **Conservación estricta de grupos manuales**: Cualquier permiso adicional otorgado a mano a un usuario fuera de su perfil se conserva intacto.
5. **Auditoría inmutable (`gnuhealth.admin.profile.log`)**: Registro de trazabilidad de cada asignación, cambio, quita o sincronización de perfiles y permisos.

---

## 2. Modelos y campos principales

### 2.1. Perfiles de Puesto
- **`gnuhealth.admin.profile`** (`admin_profile.py`):
  - `code` (`fields.Char`, requerido, unique): Identificador alfanumérico del perfil (ej. `MEDICO`, `RECEPCION`).
  - `name` (`fields.Char`, requerido): Nombre descriptivo (ej. "Médico/a", "Recepción").
  - `category` (`fields.Char`): Clasificación del perfil (Asistencial, Enfermería, Técnico, Administrativo, Farmacia).
  - `description` (`fields.Text`): Descripción del alcance funcional.
  - `active` (`fields.Boolean`, default True): Estado operativo del perfil.
  - `groups` (`fields.Many2Many` a `res.group` vía `gnuhealth.admin.profile-res.group`): Grupos que componen el perfil.
  - `apply_to_users()`: Acción de botón que invoca el asistente de sincronización masiva.

- **`gnuhealth.admin.profile-res.group`** (`admin_profile.py`):
  - Tabla relacional Many2Many con campos `profile` y `group` (ondelete CASCADE y restricción de unicidad par).

- **`gnuhealth.admin.profile.log`** (`admin_profile.py`):
  - `date` (`fields.DateTime`, requerido): Fecha y hora del evento.
  - `user` (`fields.Many2One` a `res.user`, requerido): Usuario afectado.
  - `old_profile` (`fields.Many2One` a `gnuhealth.admin.profile`): Perfil previo.
  - `new_profile` (`fields.Many2One` a `gnuhealth.admin.profile`): Perfil nuevo asignado.
  - `action` (`fields.Selection`): Tipo de acción realizada (`create`: Alta, `assign`: Asignación, `change`: Cambio, `remove`: Quita, `apply`: Aplicación masiva, `specialty`: Permisos por especialidad).
  - `groups_added` (`fields.Many2Many` a `res.group` vía `gnuhealth.admin.profile.log-res.group.added`): Permisos sumados.
  - `groups_removed` (`fields.Many2Many` a `res.group` vía `gnuhealth.admin.profile.log-res.group.removed`): Permisos revocados.

- **`gnuhealth.admin.profile.apply` y `...apply.start`** (`admin_profile.py`):
  - Asistente (`Wizard`) invocado desde el perfil de puesto para propagar masivamente sus grupos a todos los usuarios vinculados.

### 2.2. Extensión de Usuario
- **`res.user`** (Extensión con `PoolMeta` en `admin_profile.py`):
  - `admin_profile` (`fields.Many2One` a `gnuhealth.admin.profile`): Perfil asignado al usuario.
  - `extra_groups` (`fields.Function` Many2Many a `res.group`): Muestra los permisos del usuario que están por fuera de los provistos por su perfil (`current_groups - profile_groups`).
  - Interceptación en `create()` y `write()`: Calcula y aplica el delta de grupos a nivel de servidor, registrando cada suceso en el log de auditoría.

### 2.3. Áreas de Especialidad y Profesionales
- **`gnuhealth.specialty.area`** (`specialty_area.py`):
  - `code` (`fields.Char`, requerido, unique): Código único del área.
  - `name` (`fields.Char`, requerido): Nombre formal del área.
  - `groups` (`fields.Many2Many` a `res.group` vía `gnuhealth.specialty.area-res.group`): Permisos estándar asociados al área.
  - `specialties` (`fields.Many2Many` a `gnuhealth.specialty` vía `gnuhealth.specialty.area-specialty`): Especialidades que componen el área.

- **`gnuhealth.specialty.area-res.group`** (`specialty_area.py`):
  - Tabla intermedia Many2Many entre área y grupo.

- **`gnuhealth.specialty.area-specialty`** (`specialty_area.py`):
  - Tabla intermedia Many2Many entre área y especialidad médica. Posee restricción SQL `Unique(area-specialty.specialty)` para asegurar que cada especialidad pertenezca a una única área.

- **`gnuhealth.specialty`** (Extensión con `PoolMeta` en `specialty_area.py`):
  - `area` (`fields.Function` Many2One a `gnuhealth.specialty.area`): Permite consultar el área asignada a la especialidad médica.

- **`gnuhealth.healthprofessional`** (Extensión con `PoolMeta` en `specialty_area.py`):
  - Botón `apply_specialty_permissions`: Dispara la acción `health_admin_profiles.act_specialty_apply`.

- **`gnuhealth.specialty.apply` y `...apply.start`** (`specialty_area.py`):
  - Asistente (`Wizard`) que toma el profesional activo, localiza su usuario interno (`party.internal_user`), computa los grupos requeridos por las áreas de sus especialidades registradas, y tras confirmación, agrega los grupos faltantes sin modificar el perfil base ni quitar permisos existentes, asentando el evento en `gnuhealth.admin.profile.log`.

---

## 3. Perfiles base y áreas cargadas

### 3.1. Perfiles base (11 perfiles cargados en `data/profiles.xml`)
Ningún perfil base incluye el grupo de administración `res.group_admin`.

| Código | Perfil | Categoría | Grupos Asignados (`res.group`) |
|---|---|---|---|
| `RECEPCION` | Recepción | Asistencial | `health.group_health_frontdesk` |
| `MEDICO` | Médico/a | Asistencial | `health.group_health_doctor`, `health_imaging.group_health_imaging`, `health_imaging.group_health_imaging_admin`, `health_orthanc.group_imaging_orthanc` |
| `ENFERMERIA` | Enfermería | Enfermería | `health.group_health_nursing` |
| `JEFATURA_ENFERMERIA` | Jefatura de enfermería | Enfermería | `health.group_health_nursing`, `health.group_health_nursing_admin` |
| `LABORATORIO` | Laboratorio | Técnico | `health_lab.group_health_lab`, `health_lab.group_health_lab_admin` |
| `IMAGENES` | Diagnóstico por imágenes | Técnico | `health.group_health_doctor`, `health_imaging.group_health_imaging`, `health_imaging.group_health_imaging_admin`, `health_orthanc.group_imaging_orthanc` |
| `ODONTOLOGIA` | Odontología | Asistencial | `health_dentistry.group_health_dentist` |
| `TRABAJO_SOCIAL` | Trabajo social | Asistencial | `health.group_health_social_worker` |
| `FACTURACION` | Facturación | Administrativo | `health.group_health_back_office`, `account.group_account`, `party.group_party_admin` |
| `FARMACIA` | Farmacia/depósito | Farmacia | `stock.group_stock`, `stock.group_stock_admin`, `product.group_product_admin`, `purchase.group_purchase` |
| `ADMIN_SALUD` | Administración de salud | Administrativo | `health.group_health_admin`, `health.group_health_back_office`, `party.group_party_admin` |

### 3.2. Áreas de especialidad cargadas (11 áreas y 74 especialidades)
Cargadas en `data/specialty_areas.xml`, `data/specialty_areas_specialties_1.xml` y `data/specialty_areas_specialties_2.xml`:

| Código | Nombre del Área | Cant. Especialidades | Grupos por Defecto |
|---|---|:---:|---|
| `ATENCION_PRIMARIA` | Atención Primaria y Medicina General | 24 | `health.group_health_doctor` |
| `PEDIATRIA` | Pediatría y Neonatología | 4 | `health.group_health_doctor`, `health_pediatrics.group_health_pediatrics_admin` |
| `MUJER` | Ginecología, Obstetricia y Salud Sexual | 6 | `health.group_health_doctor`, `health_gyneco.group_health_gyneco_admin` |
| `CIRUGIA` | Cirugía y Especialidades Quirúrgicas | 17 | `health.group_health_doctor`, `health_surgery.group_health_surgery_admin`, `health_inpatient.group_health_inpatient_admin` |
| `IMAGENES` | Diagnóstico por Imágenes | 3 | `health.group_health_doctor`, `health_imaging.group_health_imaging`, `health_imaging.group_health_imaging_admin`, `health_orthanc.group_imaging_orthanc` |
| `LABORATORIO` | Laboratorio Clínico | 5 | `health_lab.group_health_lab`, `health_lab.group_health_lab_admin` |
| `ENFERMERIA` | Enfermería y Cuidados | 2 | `health.group_health_nursing` |
| `SALUD_MENTAL` | Salud Mental y Neurociencias | 4 | `health.group_health_doctor` |
| `ODONTOLOGIA` | Odontología y Salud Oral | 2 | `health_dentistry.group_health_dentist` |
| `COMUNITARIA` | Salud Pública, Trabajo Social y Comunidad | 2 | `health.group_health_social_worker` |
| `CIENCIAS_BASICAS` | Ciencias Básicas, Docencia e Investigación | 5 | `health_lab.group_health_lab` |
| **TOTAL** | **11 Áreas** | **74** | **100% de especialidades cubiertas (0 sin área)** |

---

## 4. Cómo se calculan los permisos

El cálculo de permisos sigue de forma estricta las reglas del proyecto:

### 4.1. Regla de transición de perfiles en `User._apply_profile()`
$$\text{Grupos Objetivo} = (\text{Grupos Actuales} - \text{Grupos Perfil Anterior}) \cup \text{Grupos Perfil Nuevo}$$
$$\text{Grupos a Quitar} = \text{Grupos Actuales} - \text{Grupos Objetivo}$$
$$\text{Grupos a Agregar} = \text{Grupos Objetivo} - \text{Grupos Actuales}$$

- Si un usuario poseía permisos otorgados de forma manual que no formaban parte de su perfil anterior, estos **nunca se eliminan** (se preservan en la resta $\text{Grupos Actuales} - \text{Grupos Perfil Anterior}$).
- Los cambios en la base de datos se ejecutan en una sola operación sobre el Many2Many: `groups: [('remove', ids_quitar), ('add', ids_agregar)]`.
- El campo `extra_groups` refleja en todo momento los grupos actuales del usuario que no pertenecen a los grupos definidos por su `admin_profile`.

### 4.2. Sincronización masiva de perfiles (`apply_profile_to_users`)
$$\text{Grupos Objetivo} = \text{Grupos Actuales} \cup \text{Grupos Perfil}$$
- Agrega a los usuarios asignados al perfil cualquier permiso faltante que haya sido sumado posteriormente al perfil, sin revocar permisos existentes.

### 4.3. Aplicación de permisos por especialidad (`ApplySpecialty`)
$$\text{Grupos a Agregar} = \text{Grupos de Áreas de Especialidades del Profesional} - \text{Grupos Actuales}$$
- Incorpora los permisos requeridos por las áreas de las especialidades del profesional a su usuario interno (`party.internal_user`), sin alterar el perfil de puesto asignado ni revocar permisos manuales o de otros puestos.

---

## 5. Seguridad y Control de Acceso

Configurado en `security/access_rights.xml`:

1. **Permisos de Lectura para todos los usuarios internos (`ir.model.access` sin grupo)**:
   - Lectura permitida (`perm_read = True`, escritura/creación/eliminación = `False`) en:
     - `gnuhealth.admin.profile`
     - `gnuhealth.admin.profile-res.group`
     - `gnuhealth.admin.profile.log`
     - `gnuhealth.admin.profile.log-res.group.added`
     - `gnuhealth.admin.profile.log-res.group.removed`
     - `gnuhealth.specialty.area`
     - `gnuhealth.specialty.area-res.group`
     - `gnuhealth.specialty.area-specialty`
2. **Permisos de Escritura, Creación y Borrado restringidos a `Administration` (`res.group_admin`)**:
   - Acceso total (`perm_read`, `perm_write`, `perm_create`, `perm_delete = True`) exclusivamente para miembros de `res.group_admin` en:
     - Perfiles de puesto (`gnuhealth.admin.profile` y tabla relacional de grupos).
     - Áreas de especialidad (`gnuhealth.specialty.area` y tablas intermedias con grupos y especialidades).
     - Asistentes de aplicación (`gnuhealth.admin.profile.apply.start`, `gnuhealth.specialty.apply.start`).
3. **Inmutabilidad y protección del Log de Auditoría**:
   - Ningún usuario ordinario ni administrador posee permisos de escritura directa en `gnuhealth.admin.profile.log`.
   - Las entradas de auditoría son generadas exclusivamente por el backend del servidor en transacciones elevadas (`with Transaction().set_user(0):`), previniendo cualquier manipulación o borrado accidental desde la interfaz.

---

## 6. Comando exacto de activación en `bd_desarrollo`

Para activar o actualizar el módulo en la base de datos de pruebas `bd_desarrollo`:

```bash
/opt/gnuhealth/his-50/venv/bin/trytond-admin -c /opt/gnuhealth/his-50/etc/trytond.conf -d bd_desarrollo -u health_admin_profiles --activate-dependencies < /dev/null
```

*(Si `trytond-admin` se encuentra en el `PATH` del entorno virtual, equivale a: `trytond-admin -c /opt/gnuhealth/his-50/etc/trytond.conf -d bd_desarrollo -u health_admin_profiles --activate-dependencies`)*.

> ⚠️ **REGLA DE SEGURIDAD:** No ejecutar este comando sobre la base de producción `health50`.

---

## 7. Estado de verificación con fecha 2026-11-05

### 7.1. Verificaciones realizadas exitosamente (2026-11-05)
1. **Verificación Estática (`verificacion/estatica.log`)**:
   - Parseo AST de código Python (.py): OK (`__init__.py`, `admin_profile.py`, `specialty_area.py`).
   - Parseo XML con `xml.dom.minidom`: OK en los 18 archivos XML del módulo (datos, seguridad, vistas).
   - Integridad con `tryton.cfg`: OK (todos los archivos listados existen físicamente).
   - Vistas `ir.ui.view`: OK (11 definiciones de vista con sus correspondientes archivos en `view/`).
   - Registro en Pool: OK (15 clases registradas correctamente en `__init__.py`).
2. **Verificación de Activación en Base de Datos**:
   - Módulo presente y en estado `activated` en `bd_desarrollo` (`estado_modulo.log`: `health_admin_profiles [('health_admin_profiles', 'activated')]`).
3. **Pruebas de Comportamiento ORM en `bd_desarrollo` (`verificacion/pruebas.log` y `pruebas_extra.log`)**:
   - Verificado con el motor real de Tryton en transacciones revertidas (`rollback`):
     - Carga íntegra de datos base: 11 áreas, 74 especialidades, 0 especialidades huérfanas.
     - Creación de usuario con perfil MEDICO y asignación automática de grupos.
     - Cambio de perfil preservando grupo manual 40.
     - Quita de perfil conservando grupo manual 40.
     - Registro y auditoría en `gnuhealth.admin.profile.log`.
     - Verificación de campo dinámico `extra_groups`.
     - Wizard de aplicación de permisos por especialidad para profesionales.
     - Sincronización masiva de perfiles reponiendo permisos faltantes.
     - Control de acceso: Usuarios sin `res.group_admin` no pueden modificar perfiles (`AccessError`).
     - Inmutabilidad: Usuarios comunes no pueden crear registros de log (`AccessError`).

### 7.2. Qué NO se verificó
- **Pruebas unitarias con test runner formal de Tryton**: No se ejecutaron pruebas con `python3 -m unittest` ni suite formal basada en `ModuleTestCase` bajo la carpeta `tests/`.
- **Renderizado visual en clientes**: No se validó la interfaz visual ni la interacción en el cliente web (SAO) ni en el cliente de escritorio Tryton mediante un navegador o sesión interactiva humana.
- **Reinicio del servidor de aplicaciones Tryton**: No se ha ejecutado el reinicio del servicio Tryton (`trytond`) en la VM (queda pendiente para el usuario administrador).
- **Base de datos productiva**: No se probó ni activó en `health50` (por protocolo estricto del proyecto).

## 8. Revisión y correcciones (2026-11-05)

Cambios hechos tras una revisión independiente del módulo:

1. **Perfiles y áreas base editables.** Antes, los datos de `data/*.xml` se
   cargaban sin `noupdate` y Tryton los bloqueaba como "configuración base":
   ni el administrador podía cambiar un nombre, quitar un grupo de un perfil
   o mover una especialidad de área. Ahora los XML usan `noupdate="1"` y
   `AdminProfile.__register__` incluye una migración que marca como editables
   los registros ya cargados (solo los de este módulo). Consecuencia: cambios
   futuros en esos XML no pisan lo que el administrador haya editado.
2. **Sincronización real de perfiles.** Nuevo campo `profile_groups` en el
   usuario (modelo `gnuhealth.admin.profile.user-res.group`) que registra los
   grupos que le otorgó el perfil. Cambiar o quitar el perfil y el botón
   "Aplicar a usuarios" **quitan** los grupos que el perfil ya no tiene,
   **agregan** los nuevos y **no tocan** los agregados a mano. "Aplicar a
   usuarios" solo deja historial de los usuarios que cambiaron. Para usuarios
   que recibieron el perfil con la versión anterior, la primera vez se toman
   como otorgados los grupos del perfil que ya tienen; desde ahí queda
   registrado.
3. **`write` con varios pares** (usuarios, valores): ahora procesa todos, no
   solo el primero.
4. **Botones restringidos.** "Aplicar a usuarios" y "Aplicar permisos de la
   especialidad" se declaran con `ir.model.button` y solo los puede usar el
   grupo `Administration` (otro usuario recibe `AccessButtonError`).
5. **Pruebas.** `tests/__init__.py` con `ModuleTestCase` y cinco pruebas
   (cambio y quita de perfil, sincronización, perfiles que comparten un grupo,
   write con varios pares, datos base editables). No se corrieron con el
   runner de Tryton.
6. **Vista previa en el formulario.** Al elegir el perfil de puesto en la
   ficha del usuario, se ven al instante los grupos que va a tener
   (`on_change_admin_profile`); al guardar, el servidor hace el mismo cálculo.
7. **Perfiles que comparten grupos.** El registro de grupos otorgados se
   escribe por diferencia, para no perder un grupo que está en el perfil
   anterior y en el nuevo.

### Verificación de las correcciones (2026-11-05)

- Activación en `bd_desarrollo`: OK. La migración dejó los 141 registros base
  (11 perfiles, 26 relaciones perfil-grupo, 11 áreas, 19 relaciones
  área-grupo y 74 área-especialidad) como editables.
- Pruebas con el motor real de Tryton en transacciones revertidas: 19 de 19
  OK (cambio entre perfiles que comparten un grupo, vista previa al elegir el
  perfil, edición de datos base, alta/cambio/quita con grupo manual, write con
  dos pares, sincronización que quita y agrega, historial sin ruido, usuario
  con perfil de la versión anterior, botón de especialidad, seguridad de
  botones y de escritura, campo Persona y regresión de la vista de persona).
- **No verificado:** las pruebas de `tests/` con el runner de Tryton y la
  vista renderizada en el cliente web. Después de actualizar hay que
  reiniciar el servidor (`sudo systemctl restart gnuhealth.service`).
