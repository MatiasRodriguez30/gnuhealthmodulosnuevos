# Cómo llevar los módulos nuevos a la VM de prácticas

Este README explica cómo copiar y activar los módulos que hicimos en la VM de
GNU Health 5.0 / Tryton 7.0.

> Importante: los comandos de activación van **solo contra `bd_desarrollo`**.
> No ejecutar nada sobre `health50` sin autorización.

---

## 1. Qué módulos hay que llevar

| Módulo | Estado | Qué hace |
|---|---|---|
| `health_admin_profiles` | Nuevo | Perfiles de puesto, áreas de especialidad y botón de permisos en la ficha del profesional. |
| `health_user_person` | Nuevo (versión simplificada) | Agrega el campo **Persona** en el usuario para buscar/vincular una persona. El alta se hace con el **“Crear…”** estándar de Tryton. |
| `persona_datos_obligatorios` | Ya existía | Exige nombre, apellido, email, teléfono y domicilio al crear una persona. |
| `persona_tipo_sangre` | Ya existía | Grupo y factor Rh en la persona. |
| `persona_tipos_documento` | Ya existía | Tipos de documento (DNI, CUIT, etc.). |
| `persona_alta_ordenada` | Ya existía | Bloque de “Datos de alta” en el formulario de persona. |

Los seis módulos están incluidos en este repositorio. Los dos primeros son
los que hicimos en este trabajo; los cuatro `persona_*` ya existían antes y se
incluyen para que la VM de prácticas quede completa.

---

## 2. Estructura de carpetas esperada

Dentro del repositorio del proyecto:

```text
proyecto_equipo/
├── modulos_propios/
│   ├── health_admin_profiles/
│   │   ├── __init__.py
│   │   ├── tryton.cfg
│   │   ├── admin_profile.py
│   │   ├── specialty_area.py
│   │   ├── health_admin_profiles.xml
│   │   ├── health_specialty_areas.xml
│   │   ├── data/
│   │   │   ├── profiles.xml
│   │   │   ├── specialty_areas.xml
│   │   │   ├── specialty_areas_specialties_1.xml
│   │   │   └── specialty_areas_specialties_2.xml
│   │   ├── security/
│   │   │   └── access_rights.xml
│   │   └── view/
│   │       ├── admin_profile_form.xml
│   │       ├── admin_profile_tree.xml
│   │       ├── admin_profile_log_form.xml
│   │       ├── admin_profile_log_tree.xml
│   │       ├── admin_profile_apply_form.xml
│   │       ├── user_form.xml
│   │       ├── specialty_area_form.xml
│   │       ├── specialty_area_tree.xml
│   │       ├── specialty_apply_form.xml
│   │       ├── healthprofessional_form.xml
│   │       └── specialty_form.xml
│   │
│   ├── health_user_person/
│   │   ├── __init__.py
│   │   ├── tryton.cfg
│   │   ├── user_person.py
│   │   ├── user_person.xml
│   │   └── view/
│   │       └── user_form_person.xml
│   │
│   ├── persona_datos_obligatorios/
│   ├── persona_tipo_sangre/
│   ├── persona_tipos_documento/
│   └── persona_alta_ordenada/
│
└── ... (Fede/, Mati/, Gonza/, Lea/, Jonny/, etc.)
```

Cada carpeta de módulo **debe** tener su `tryton.cfg`. No metas carpetas que no
sean módulos dentro de `modulos_propios/`.

---

## 3. Copiar los módulos a la VM

### Opción A: la VM ya ve el repo por carpeta compartida

En este entorno el repo está en:

- Host: `/srv/datos/gnuhealth/proyecto_equipo`
- VM: `/media/sf_proyecto_equipo`

Si en la VM de prácticas la ruta es otra, ajustá `REPO_VM`.

```bash
REPO_VM=/media/sf_proyecto_equipo
ls "$REPO_VM/modulos_propios"
```

Si los módulos ya están en el repo, no hay que copiar nada: la VM los ve por la
carpeta compartida.

### Opción B: copiar desde el host a la VM por SSH

Desde el host, con acceso SSH a la VM:

```bash
REPO_DESTINO=/media/sf_proyecto_equipo/modulos_propios

scp -P 2222 -r \
  /srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_admin_profiles \
  /srv/datos/gnuhealth/proyecto_equipo/modulos_propios/health_user_person \
  /srv/datos/gnuhealth/proyecto_equipo/modulos_propios/persona_datos_obligatorios \
  /srv/datos/gnuhealth/proyecto_equipo/modulos_propios/persona_tipo_sangre \
  /srv/datos/gnuhealth/proyecto_equipo/modulos_propios/persona_tipos_documento \
  /srv/datos/gnuhealth/proyecto_equipo/modulos_propios/persona_alta_ordenada \
  gnuhealth@192.168.1.44:"$REPO_DESTINO/"
```

### Opción C: usar el paquete ya preparado

En esta misma carpeta dejé un paquete con los seis módulos, sin
`__pycache__` ni logs de verificación:

```text
modulos_nuevos.tar.gz
```

Contiene:

```text
health_admin_profiles/
health_user_person/
persona_datos_obligatorios/
persona_tipo_sangre/
persona_tipos_documento/
persona_alta_ordenada/
```

Para descomprimirlo en la VM:

```bash
cd /media/sf_proyecto_equipo/modulos_propios
tar -xzf /ruta/a/modulos_nuevos.tar.gz
```

### Opción D: copiar a otro repo

Si me pasás otro repositorio, copio las carpetas respetando esta estructura:

```text
<otro-repo>/modulos_propios/health_admin_profiles/
<otro-repo>/modulos_propios/health_user_person/
```

No hace falta que el repo tenga git en la VM. En el host sí se puede usar git
para clonar/actualizar y después copiar por la carpeta compartida o por `scp`.

---

## 4. Enlazar los módulos en Tryton

Dentro de la VM:

```bash
TRYTON_MODULES=/opt/gnuhealth/his-50/venv/lib/python3.11/site-packages/trytond/modules
REPO_VM=/media/sf_proyecto_equipo

for m in health_admin_profiles health_user_person; do
    if [ ! -e "$TRYTON_MODULES/$m" ]; then
        ln -s "$REPO_VM/modulos_propios/$m" "$TRYTON_MODULES/$m"
    fi
done
```

Verificar:

```bash
ls -l "$TRYTON_MODULES/health_admin_profiles" "$TRYTON_MODULES/health_user_person"
```

El enlace tiene que apuntar a la carpeta real del módulo. No uses `ln -f` si ya
existe: primero revisá qué hay.

---

## 5. Activar en la base de pruebas

Siempre en `bd_desarrollo`:

```bash
TRYTON_ADMIN=/opt/gnuhealth/his-50/venv/bin/trytond-admin
CONF=/opt/gnuhealth/his-50/etc/trytond.conf

$TRYTON_ADMIN -c "$CONF" -d bd_desarrollo \
  -u health_admin_profiles --activate-dependencies < /dev/null

$TRYTON_ADMIN -c "$CONF" -d bd_desarrollo \
  -u health_user_person --activate-dependencies < /dev/null
```

`trytond-admin` puede no imprimir nada si termina bien. El código de salida
debe ser `0`.

Si vas a activar también los módulos de persona:

```bash
for m in persona_datos_obligatorios persona_tipo_sangre \
         persona_tipos_documento persona_alta_ordenada; do
    $TRYTON_ADMIN -c "$CONF" -d bd_desarrollo \
      -u "$m" --activate-dependencies < /dev/null
done
```

---

## 6. Reiniciar el servidor

El servidor en ejecución **no recarga el código Python**. Después de copiar o
actualizar los módulos:

```bash
sudo systemctl restart gnuhealth.service
```

Luego, en la web:

1. Entrar a `http://192.168.1.44:8400/`.
2. Elegir la base **`bd_desarrollo`**.
3. Recargar con `Ctrl+F5`.

---

## 7. Dónde se ve cada cosa

### `health_admin_profiles`

- **Perfiles de puesto**: `Health` → `Configuration` → **Perfiles de puesto**.
- **Historial de perfiles**: `Health` → `Configuration` → **Historial de perfiles**.
- **Áreas de especialidad**: `Health` → `Configuration` → `Misc` → **Áreas de especialidad**.
- **Perfil en el usuario**: abrir un usuario → solapa **Access Permissions** →
  campo **Perfil de puesto** y **Grupos extra**.
- **Botón del profesional**: `Health` → `Configuration` → `Health Professionals`
  → abrir un profesional → **“Aplicar permisos de la especialidad”**.

### `health_user_person`

- Abrir un usuario.
- Arriba aparece **Persona**.
- La lupa busca personas existentes.
- El desplegable **“Crear…”** abre el formulario estándar de persona.
- Al guardar, la persona queda vinculada al usuario por `internal_user`.

---

## 8. Verificación rápida

Después de activar, se puede comprobar que el módulo quedó activado con:

```bash
/opt/gnuhealth/his-50/venv/bin/python -I -B - <<'PY'
from trytond.config import config
config.update_etc("/opt/gnuhealth/his-50/etc/trytond.conf")
from trytond.pool import Pool
from trytond.transaction import Transaction
DB = "bd_desarrollo"
pool = Pool(DB); pool.init()
with Transaction().start(DB, 1, context={"company": 1}, readonly=True):
    M = pool.get("ir.module")
    for name in ("health_admin_profiles", "health_user_person"):
        print([(x.name, x.state) for x in M.search([("name", "=", name)])])
PY
```

Debe mostrar `activated` para los dos módulos.

---

## 9. Cosas a tener en cuenta

- No copies `__pycache__/` ni archivos `.pyc` al repo. Se pueden borrar antes de
  empaquetar.
- No copies las capturas de pantalla ni PDFs dentro de los módulos.
- `health_admin_profiles` depende de que estén instalados `health_lab`,
  `health_imaging`, `health_orthanc`, `health_dentistry`, `health_gyneco`,
  `health_pediatrics`, `health_surgery`, `health_inpatient`, `account`, `stock`
  y `purchase`.
- `health_user_person` depende de `health` y `party`.
- No tocar `health50`. Todo se prueba en `bd_desarrollo`.
- No hay contraseñas en este README ni en el código.
- Si el repo de prácticas ya tiene otros módulos, no los pises: copiá solo las
  carpetas nuevas o hacé un backup antes.

---

## 10. Contenido de este repositorio

```text
.
├── README.md
├── modulos_nuevos.tar.gz
├── .gitignore
└── modulos_propios/
    ├── health_admin_profiles/
    ├── health_user_person/
    ├── persona_datos_obligatorios/
    ├── persona_tipo_sangre/
    ├── persona_tipos_documento/
    └── persona_alta_ordenada/
```
