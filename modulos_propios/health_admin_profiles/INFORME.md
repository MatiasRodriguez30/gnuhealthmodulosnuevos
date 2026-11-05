# Informe de Verificación y Documentación: health_admin_profiles

**Fecha:** 2026-11-05  
**Módulo:** `health_admin_profiles` (GNU Health 5.0 / Tryton 7.0 / Python 3.11)  
**Contexto de tarea:** Documentación veraz y reporte de evidencia posterior a activación y pruebas (`happ-09-activar-probar`).

---

## 1. Lista de archivos creados y modificados (rutas absolutas)

### 1.1. Estructura del módulo en producción local
Ruta base del módulo: `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/`

- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/__init__.py` (Registro de 15 modelos y wizards en el Pool)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/tryton.cfg` (Definición del módulo, versión 7.0.0, 12 dependencias y lista de 7 archivos XML)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/admin_profile.py` (Lógica de perfiles de puesto, logs, extensión de `res.user`, wizards)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/specialty_area.py` (Lógica de áreas de especialidad, extensión de especialidades, extensión de `gnuhealth.healthprofessional` y wizards)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/health_admin_profiles.xml` (Acciones de ventana, vistas y menús de perfiles y logs)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/health_specialty_areas.xml` (Acciones de ventana, vistas y menús de áreas de especialidad)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/security/access_rights.xml` (Reglas de acceso `ir.model.access` para lectura general y escritura admin)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/data/profiles.xml` (Definición de los 11 perfiles de puesto y asociación con grupos)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/data/specialty_areas.xml` (Definición de las 11 áreas de especialidad y sus grupos)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/data/specialty_areas_specialties_1.xml` (Asignación de especialidades a áreas, parte 1)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/data/specialty_areas_specialties_2.xml` (Asignación de especialidades a áreas, parte 2)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/view/admin_profile_form.xml` (Vista formulario de perfil de puesto)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/view/admin_profile_tree.xml` (Vista lista de perfil de puesto)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/view/admin_profile_log_form.xml` (Vista formulario de log de perfil)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/view/admin_profile_log_tree.xml` (Vista lista de log de perfil)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/view/admin_profile_apply_form.xml` (Vista de inicio de wizard de aplicación masiva)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/view/user_form.xml` (Vista heredada de `res.user` con campos de perfil y grupos extra)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/view/specialty_area_form.xml` (Vista formulario de área de especialidad)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/view/specialty_area_tree.xml` (Vista lista de área de especialidad)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/view/specialty_form.xml` (Vista heredada de especialidad médica con área)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/view/specialty_apply_form.xml` (Vista de inicio de wizard de permisos por especialidad)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/view/healthprofessional_form.xml` (Vista heredada de profesional de la salud con botón)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/README.md` (Documentación técnica integral del módulo)
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/INFORME.md` (Copia del presente informe dentro del módulo)

### 1.2. Archivos de verificación y registro en el módulo
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/verificacion/estatica.log`
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/verificacion/activacion.log`
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/verificacion/pruebas.log`
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/verificacion/estado_modulo.log`
- `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/verificacion/pruebas_extra.log`

### 1.3. Archivos en el espacio de trabajo actual (`/srv/datos/cambiosgnu/`)
- `/srv/datos/cambiosgnu/README.md`
- `/srv/datos/cambiosgnu/INFORME.md`
- `/srv/datos/cambiosgnu/verificacion/estatica.log`
- `/srv/datos/cambiosgnu/verificacion/activacion.log`
- `/srv/datos/cambiosgnu/verificacion/pruebas.log`
- `/srv/datos/cambiosgnu/SUPERPROMPT_IA_perfiles_y_especialidades.md`
- `/srv/datos/cambiosgnu/GUIA_LAN_MATIAS.pdf`

---

## 2. Comandos ejecutados y base usada

### 2.1. Base de datos utilizada
Todas las activaciones y pruebas de comportamiento fueron ejecutadas exclusivamente contra la base de datos de pruebas **`bd_desarrollo`**.  
Bajo ningún concepto se operó sobre la base de datos productiva `health50`.

### 2.2. Comandos ejecutados

1. **Chequeo estático de código Python mediante AST:**
   ```bash
   python3 -I -B -c "import ast, glob; [ast.parse(open(f).read(), filename=f) for f in glob.glob('/srv/datos/gnuhealth/proyecto_equipo/Mati/health_admin_profiles/*.py')]"
   ```
2. **Chequeo estático de sintaxis XML mediante `xml.dom.minidom`:**
   ```bash
   python3 -I -B -c "import glob, xml.dom.minidom; [xml.dom.minidom.parse(f) for f in glob.glob('/srv/datos/gnuhealth/proyecto_equipo/Mati/health_admin_profiles/**/*.xml', recursive=True)]"
   ```
3. **Activación y actualización del módulo en `bd_desarrollo`:**
   ```bash
   /opt/gnuhealth/his-50/venv/bin/trytond-admin -c /opt/gnuhealth/his-50/etc/trytond.conf -d bd_desarrollo -u health_admin_profiles --activate-dependencies < /dev/null
   ```
4. **Verificación de estado de instalación del módulo:**
   Ejecutado por script Python contra `ir.module`:
   ```python
   Module.search([('name', '=', 'health_admin_profiles')])[0].state
   # Resultado: 'activated'
   ```
5. **Ejecución de pruebas de comportamiento ORM vía SSH en transacciones revertidas (`rollback`):**
   ```bash
   ssh -p 2222 gnuhealth@192.168.1.44 "/opt/gnuhealth/his-50/venv/bin/python -I -B -" << 'EOF'
   # Script de prueba ORM ejecutado con rollback()
   EOF
   ```

---

## 3. Evidencia documental de verificación

A continuación se detalla la evidencia concreta de los archivos de registro disponibles:

### 3.1. `verificacion/estatica.log`
- **Ruta de archivo:** `/srv/datos/cambiosgnu/verificacion/estatica.log`  
  *(y `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/verificacion/estatica.log`)*
- **Tamaño:** 5.674 bytes.
- **Resumen textual veraz de lo que muestra:**
  El log contiene 5 chequeos exhaustivos con resultado final exitoso (`ESTADO GENERAL: OK`):
  - **Chequeo 1 (AST Python):** Parseo correcto sin errores sintácticos de `__init__.py`, `admin_profile.py` y `specialty_area.py`.
  - **Chequeo 2 (Parseo XML minidom):** 18 archivos XML procesados con éxito (vistas, datos base de perfiles, áreas y especialidades, y permisos de acceso).
  - **Chequeo 3 (Coherencia tryton.cfg):** Los 7 archivos XML declarados en la sección `xml:` existen físicamente.
  - **Chequeo 4 (Vistas ir.ui.view):** 11 registros `ir.ui.view` validados con sus archivos XML correspondientes en la carpeta `view/`.
  - **Chequeo 5 (Pool.register):** Las 15 clases definidas en los módulos Python (`AdminProfile`, `AdminProfileGroup`, `AdminProfileLogGroupAdded`, `AdminProfileLogGroupRemoved`, `AdminProfileLog`, `User`, `ApplyProfileStart`, `ApplyProfile`, `SpecialtyArea`, `SpecialtyAreaGroup`, `SpecialtyAreaSpecialty`, `Specialty`, `HealthProfessional`, `ApplySpecialtyStart`, `ApplySpecialty`) coinciden y están registradas en el Pool de Tryton.

### 3.2. `verificacion/activacion.log`
- **Ruta de archivo:** `/srv/datos/cambiosgnu/verificacion/activacion.log`  
  *(y `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/verificacion/activacion.log`)*
- **Tamaño:** 0 bytes (archivo vacío).
- **Resumen textual veraz de lo que muestra:**
  El archivo se encuentra **vacío (0 bytes)**. La activación en la base de datos `bd_desarrollo` fue efectivamente completada durante la fase previa de la tarea de activación (como lo corrobora el archivo complementario `verificacion/estado_modulo.log`, donde figura `health_admin_profiles [('health_admin_profiles', 'activated')]`), pero el comando no volcó salida estándar o la redirección al archivo `activacion.log` no capturó texto. Se reporta explícitamente esta situación sin inventar registros que no existan.

### 3.3. `verificacion/pruebas.log`
- **Ruta de archivo:** `/srv/datos/cambiosgnu/verificacion/pruebas.log`  
  *(y `/srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles/verificacion/pruebas.log`)*
- **Tamaño:** 5.489 bytes.
- **Resumen textual veraz de lo que muestra:**
  Contiene el reporte detallado de las pruebas de comportamiento ORM sobre `bd_desarrollo`, estructurado en 5 secciones:
  1. **Ejecución verbatim del script original:** Arrojó 2 casos `OK` y 5 casos `FALLA`.
     - Casos OK: `datos base: 11 areas y 74 especialidades` y `areas con grupos y especialidades`.
     - Casos FALLA: Los 5 casos de creación y manipulación de usuarios fallaron con `PasswordError: The password must have at least 8 characters.`.
  2. **Tabla de resultados verbatim:** Tabulación de los 7 casos con el error mencionado.
  3. **Análisis de causa raíz:** Explica que la falla provino exclusivamente de una restricción de validación interna del núcleo de Tryton 7.0 (`trytond/res/user.py`), donde por defecto la longitud mínima de contraseña es de 8 caracteres (`config.getint('password', 'length', default=0)` toma `8`). Como el script suministrado intentaba crear usuarios con `'password': 'test'` (4 caracteres), Tryton disparó `PasswordError` antes de interactuar con la lógica del módulo. No fue un error del módulo `health_admin_profiles`.
  4. **Ejecución con contraseña válida (>= 8 caracteres):** Utilizando `'password': 'testpassword'`, todos los 7 casos completaron exitosamente:
     - `datos base: 11 areas y 74 especialidades`: OK (`perfiles=11 areas=11 especialidades=74 relaciones=74 sin_area=[]`).
     - `crear usuario con perfil MEDICO`: OK (asigna grupos `[7, 34, 35, 41]`).
     - `cambiar perfil conserva grupo manual 40`: OK (grupos resultantes `[16, 17, 40]`).
     - `quitar perfil conserva grupo manual 40`: OK (grupos resultantes `[40]`).
     - `log de cambio de perfil`: OK (`logs=1 acciones=['assign']`).
     - `areas con grupos y especialidades`: OK (las 11 áreas correctamente enlazadas con grupos y especialidades).
     - `extra_groups muestra solo los grupos fuera del perfil`: OK (`extra=[40]`).
  5. **Tabla de resultados final:** Tabulación de los 7 casos en estado `OK`.

### 3.4. Evidencia complementaria en el módulo (`estado_modulo.log` y `pruebas_extra.log`)
- `estado_modulo.log`: Confirma que `health_admin_profiles` y sus módulos dependientes (`health`, `health_lab`, `health_imaging`, `health_orthanc`, `health_dentistry`, `health_gyneco`, `health_pediatrics`, `health_surgery`, `health_inpatient`, `account`, `stock`, `purchase`) se encuentran en estado `activated` en `bd_desarrollo`.
- `pruebas_extra.log`: Confirma 4 casos adicionales en estado `OK`:
  - Wizard de especialidad calcula áreas y grupos de un profesional (`user=admin areas=['Atención Primaria y Medicina General'] grupos=['Health Doctor'] ids=[7]`).
  - Aplicar perfil a usuarios repone grupos faltantes (`cambiados=1 grupos=[6]`).
  - Seguridad: Usuario sin `res.group_admin` NO puede modificar perfiles (`AccessError`).
  - Seguridad: Usuario común NO puede crear registros de log de perfiles (`AccessError`).

---

## 4. Qué NO se verificó

Conforme al estándar de transparencia y fidelidad del proyecto:
1. **Runner de pruebas unitarias de Tryton:** No se ejecutaron pruebas con el motor de pruebas unitarias formal de Tryton (`trytond.tests.test_tryton` / `python3 -m unittest`) ni existe una carpeta `tests/` con clases `ModuleTestCase`.
2. **Inspección visual en cliente Web (SAO) o de Escritorio:** No se abrió el navegador web ni se manipuló la interfaz gráfica humana para verificar renderizado en pantalla de formularios, botones, diálogos modales ni estilos CSS.
3. **Reinicio del demonio Tryton en la VM:** No se ejecutó el comando de reinicio del servicio de Tryton en el sistema operativo de la máquina virtual.
4. **Base de datos productiva:** No se activó ni testeó en `health50`.

---

## 5. Pasos pendientes para el usuario

Para poner el módulo plenamente a disposición de los usuarios finales en el entorno de desarrollo:

1. **Reiniciar el servidor Tryton:**
   Dentro de la máquina virtual (o mediante el servicio correspondiente), reiniciar el demonio de Tryton para que el proceso cargue en memoria el código Python nuevo de `health_admin_profiles`:
   ```bash
   sudo systemctl restart gnuhealth.service
   ```
   *(o la directiva de supervisor/servicio que corresponda en la VM).*

2. **Recargar el cliente Web (SAO) / Reconectar cliente de escritorio:**
   - En el navegador web, forzar la recarga limpia de caché con `Ctrl + F5` (o `Cmd + Shift + R`) para asegurar que se descarguen las nuevas definiciones de vistas, botones y asistentes.
   - En el cliente de escritorio Tryton, cerrar la sesión y volver a iniciarla.

3. **Control de versiones (Git):**
   Revisar el estado del árbol de trabajo con `git status` y efectuar el commit correspondiente con los cambios aprobados:
   ```bash
   git status
   git add modulos_propios/health_admin_profiles
   git commit -m "docs(health_admin_profiles): agregar README completo e informe de verificacion"
   ```
