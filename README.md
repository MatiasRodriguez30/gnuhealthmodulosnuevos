# Módulos nuevos para GNU Health 5.0 (Tryton 7.0)

Guía para instalar estos seis módulos en una VM con GNU Health 5.0, por
ejemplo **la VM del hospital**. Está escrita para seguirla de arriba hacia abajo
copiando los comandos. Lo que cambia de una VM a otra (rutas, base, servicio)
se define una sola vez en el paso 2.

> **Importante**
> - Probá siempre primero en una **base de pruebas**, nunca directo en la base
>   que se usa con pacientes reales.
> - Hacé el **backup del paso 4** antes de activar nada.
> - No hay contraseñas en esta guía ni en el código.

---

## Resumen (checklist)

1. Leer qué cambia en el sistema (paso 1).
2. Completar los datos de la VM (paso 2).
3. Verificar que estén los módulos de GNU Health necesarios (paso 3).
4. Hacer backup de la base (paso 4).
5. Descargar y descomprimir los módulos (paso 5).
6. Enlazarlos en Tryton (paso 6).
7. Activarlos en la base de pruebas (paso 7).
8. Reiniciar el servidor (paso 8).
9. Verificar y probar en la web (paso 9).

---

## 1. Qué módulos son y qué cambian

| Módulo | Qué hace |
|---|---|
| `health_admin_profiles` | Perfiles de puesto (Recepción, Médico/a, Enfermería, etc.) que asignan grupos de permisos; áreas de especialidad; historial de cambios; botón "Aplicar permisos de la especialidad" en el profesional. |
| `health_user_person` | Campo **Persona** en la ficha del usuario para vincularlo con una persona. |
| `persona_datos_obligatorios` | Al **crear** una persona exige nombre, apellido, email, teléfono y domicilio. |
| `persona_tipo_sangre` | Grupo sanguíneo y factor Rh en la persona (se copia al paciente si el paciente no lo tiene). |
| `persona_tipos_documento` | Tipos de documento DNI, CUIT, CUIL, LE, LC, pasaporte y cédula, y carga rápida de tipo y número. |
| `persona_alta_ordenada` | Bloque "Datos de alta" (Documento, Contacto, Domicilio, Grupo sanguíneo) en el formulario de persona. |

**Cambio de comportamiento a avisar al equipo:** con `persona_datos_obligatorios`
activo, **toda persona nueva** (incluidos pacientes) necesita apellido, email,
teléfono y domicilio con calle para poder guardarse. Las personas que ya existen
se pueden seguir editando sin completar esos datos.

**Dependencias.** `health_admin_profiles` necesita estos módulos de GNU Health:
`health`, `health_lab`, `health_imaging`, `health_orthanc`, `health_dentistry`,
`health_gyneco`, `health_pediatrics`, `health_surgery`, `health_inpatient`,
`account`, `stock` y `purchase`. Los demás solo necesitan `health` y `party`.
Si alguno no está activado, la activación (paso 7) lo activa, siempre que su
código exista en la VM (eso se verifica en el paso 3).

---

## 2. Datos de la VM

Todos los comandos siguientes se corren **dentro de la VM**, con el usuario que
administra GNU Health (en la VM de prácticas es `gnuhealth`).

Averiguá cada dato con estos comandos:

```bash
# Comando con el que corre el servidor Tryton (muestra el venv y, si figura, el -c del config)
ps -eo args | grep "[b]in/trytond"

# Configuraciones de Tryton disponibles
ls /opt/gnuhealth/*/etc/trytond.conf

# Bases de datos (elegí la de PRUEBAS)
psql -l

# Nombre del servicio del servidor
systemctl list-units --type=service | grep -iE "gnuhealth|tryton"
```

Después completá y pegá este bloque (los valores de ejemplo son los de la VM de
prácticas):

```bash
VENV=/opt/gnuhealth/his-50/venv
CONF=/opt/gnuhealth/his-50/etc/trytond.conf
DB=bd_desarrollo
SERVICIO=gnuhealth.service
MODULOS_DIR="$HOME/modulos_propios"

TRYTON_ADMIN="$VENV/bin/trytond-admin"
TRYTON_MODULES="$("$VENV/bin/python" -c 'import os, trytond.modules as m; print(os.path.dirname(m.__file__))')"
MODULOS="health_admin_profiles health_user_person persona_datos_obligatorios persona_tipo_sangre persona_tipos_documento persona_alta_ordenada"

echo "Módulos de Tryton en: $TRYTON_MODULES"
```

`MODULOS_DIR` es la carpeta donde van a quedar los módulos. Si la VM ya tiene
una carpeta de módulos propios (por ejemplo, un repo compartido con
`modulos_propios/`), usá esa.

---

## 3. Verificar dependencias

```bash
for m in health health_lab health_imaging health_orthanc health_dentistry \
         health_gyneco health_pediatrics health_surgery health_inpatient \
         account stock purchase party; do
    if [ -d "$TRYTON_MODULES/$m" ]; then echo "ok    $m"; else echo "FALTA $m"; fi
done
```

Si aparece alguna **FALTA**, no sigas: ese módulo de GNU Health no está
instalado en la VM y lo tiene que instalar quien la administre.

Comprobá también quién es dueño de la carpeta de módulos de Tryton (hace falta
para el paso 6):

```bash
stat -c "dueño: %U" "$TRYTON_MODULES"; whoami
```

---

## 4. Backup de la base (obligatorio)

```bash
pg_dump -Fc -d "$DB" -f "$HOME/backup_${DB}_$(date +%F_%H%M).dump"
ls -lh "$HOME"/backup_"$DB"_*.dump
```

Si algo sale mal, quien administre la VM puede restaurarla con `pg_restore`
en una base nueva. No sigas si el backup no se generó.

---

## 5. Descargar los módulos

**Opción A: con git**

```bash
cd "$HOME"
git clone https://github.com/MatiasRodriguez30/gnuhealthmodulosnuevos.git
mkdir -p "$MODULOS_DIR"
cp -r gnuhealthmodulosnuevos/modulos_propios/* "$MODULOS_DIR"/
```

**Opción B: sin git (descarga del paquete)**

```bash
mkdir -p "$MODULOS_DIR" && cd "$MODULOS_DIR"
curl -L -o modulos_nuevos.tar.gz \
  https://github.com/MatiasRodriguez30/gnuhealthmodulosnuevos/raw/main/modulos_nuevos.tar.gz
tar -xzf modulos_nuevos.tar.gz && rm modulos_nuevos.tar.gz
```

Si la VM no tiene internet, descargá `modulos_nuevos.tar.gz` desde la página
del repositorio en otra PC y copialo a la VM (con `scp`, un pendrive o la
carpeta compartida), y después descomprimilo con el `tar` de arriba.

**Si ya había una versión anterior de estos módulos**, guardala antes de
reemplazarla (por ejemplo, `mv "$MODULOS_DIR/health_admin_profiles" "$HOME/health_admin_profiles.anterior"`).

Comprobá que quedaron los seis, cada uno con su `tryton.cfg`:

```bash
for m in $MODULOS; do
    if [ -f "$MODULOS_DIR/$m/tryton.cfg" ]; then echo "ok    $m"; else echo "FALTA $m"; fi
done
```

---

## 6. Enlazar los módulos en Tryton

Tryton solo ve los módulos que están en su carpeta de módulos. Se enlazan (no se
copian), así una actualización solo requiere reemplazar la carpeta:

```bash
for m in $MODULOS; do
    if [ -e "$TRYTON_MODULES/$m" ]; then
        echo "ya existe: $m -> $(readlink "$TRYTON_MODULES/$m")"
    else
        ln -s "$MODULOS_DIR/$m" "$TRYTON_MODULES/$m" && echo "enlazado: $m"
    fi
done
```

Si el paso 3 mostró que el dueño de la carpeta de módulos **no** es tu usuario,
este paso lo tiene que hacer quien administre la VM. Si algún módulo dice "ya
existe", revisá a dónde apunta antes de tocarlo; no uses `ln -f`.

---

## 7. Activar en la base de pruebas

```bash
"$TRYTON_ADMIN" -c "$CONF" -d "$DB" -u $MODULOS --activate-dependencies \
  < /dev/null > "$HOME/activacion_modulos.log" 2>&1
echo "código de salida: $?"
```

- Código **0**: terminó bien (es normal que el log quede vacío o con avisos).
- Otro código: mirá el final del log con `tail -40 "$HOME/activacion_modulos.log"`.

Confirmá el estado en la base:

```bash
psql -d "$DB" -c "select name, state from ir_module where name in ('health_admin_profiles','health_user_person','persona_datos_obligatorios','persona_tipo_sangre','persona_tipos_documento','persona_alta_ordenada') order by name;"
```

Los seis tienen que decir `activated`.

---

## 8. Reiniciar el servidor

El servidor en ejecución **no carga el código nuevo** hasta reiniciarlo:

```bash
sudo systemctl restart "$SERVICIO"
systemctl is-active "$SERVICIO"
journalctl -u "$SERVICIO" -n 30 --no-pager
```

Después entrá a GNU Health desde el navegador (la misma dirección de siempre),
elegí la **base de pruebas** en el inicio de sesión y recargá con `Ctrl+F5`.

---

## 9. Dónde se ve cada cosa (menús en español)

| Qué | Dónde |
|---|---|
| Perfiles de puesto | Salud > Configuración > **Perfiles de puesto** |
| Historial de cambios de perfil | Salud > Configuración > **Historial de perfiles** |
| Áreas de especialidad | Salud > Configuración > Misc > **Áreas de especialidad** |
| Área de cada especialidad | Salud > Configuración > Misc > Especialidades Médicas |
| Perfil en el usuario | Administración > Usuarios > Usuarios > pestaña de permisos: **Perfil de puesto**, **Grupos otorgados por el perfil**, **Grupos extra** |
| Persona del usuario | Administración > Usuarios > Usuarios > campo **Persona** (arriba) |
| Botón de especialidad | Salud > Profesionales de la salud > abrir un profesional > **Aplicar permisos de la especialidad** |
| Alta de persona | Terceros > Personas > nueva: bloque **Datos de alta** |

**Prueba rápida:**

1. En un usuario de prueba elegí el perfil "Recepción": los grupos se completan
   al instante (antes de guardar).
2. Agregale un grupo a mano, guardá y cambiá el perfil a "Médico/a": el grupo
   manual tiene que quedar.
3. En "Perfiles de puesto" editá un perfil y guardá: tiene que dejar.
4. Creá una persona sin email: tiene que pedirlo.

Los botones "Aplicar a usuarios" y "Aplicar permisos de la especialidad" solo
los puede usar el grupo `Administration`.

---

## 10. Si algo sale mal

| Síntoma | Qué hacer |
|---|---|
| El paso 7 dice que no encuentra un módulo propio | El enlace del paso 6 falta o apunta mal: `ls -l "$TRYTON_MODULES" \| grep -E "health_admin\|health_user\|persona_"`. |
| El paso 7 falla en un módulo de GNU Health (por ejemplo `health_orthanc`) | Puede necesitar paquetes de Python que la VM no tiene. Pasale el final del log a quien administre la VM. |
| Los cambios no aparecen en la web | Falta el reinicio del paso 8, o estás en otra base: elegí la de pruebas al iniciar sesión. |
| La ficha de usuario o de persona da error después de actualizar | Reiniciá el servidor (paso 8) y recargá con `Ctrl+F5`. |
| Hay que volver atrás | Quien administre la VM restaura el backup del paso 4. |

---

## Referencia: VM de prácticas

- Repo compartido: host `/srv/datos/gnuhealth/proyecto_equipo`, VM
  `/media/sf_proyecto_equipo` (los módulos van en `modulos_propios/`, así que
  ahí `MODULOS_DIR=/media/sf_proyecto_equipo/modulos_propios`).
- Base de pruebas: `bd_desarrollo`. La base principal `health50` no se toca.
- Servicio: `gnuhealth.service`.
- En esa VM la carpeta de módulos de Tryton pertenece al usuario `gnuhealth`,
  así que el enlace del paso 6 se hace sin `sudo`.

---

## Novedades del 2026-11-05

Correcciones de `health_admin_profiles` después de una revisión con pruebas
contra la base:

- Los perfiles y áreas que vienen cargados ahora **se pueden editar** desde la
  interfaz (antes Tryton los bloqueaba como configuración base). Si el módulo
  ya estaba instalado, la actualización (`-u`) los marca como editables.
- "Aplicar a usuarios" y el cambio de perfil **sincronizan de verdad**: quitan
  los grupos que se sacaron del perfil, agregan los nuevos y no tocan los
  agregados a mano. El usuario muestra "Grupos otorgados por el perfil".
- Al elegir un perfil en la ficha del usuario, los grupos se ven al instante.
- Los botones "Aplicar a usuarios" y "Aplicar permisos de la especialidad"
  solo los puede usar el grupo `Administration`.
- `health_user_person`: la búsqueda por Persona resuelve "sin persona" y
  "con persona".
- Ambos módulos tienen pruebas en `tests/` (`ModuleTestCase`).
- "Historial de perfiles" ya no da `KeyError: 'datetime'` en el cliente
  Tryton 7.0: la lista muestra la fecha y la hora en dos columnas (el cliente
  no tiene widget de fecha y hora en listas). Si ya estaba instalado:
  reemplazá la carpeta, actualizá con `-u health_admin_profiles`, reiniciá el
  servidor y cerrá y abrí el cliente.

Si ya tenías una versión anterior instalada: reemplazá las carpetas (paso 5),
actualizá con el paso 7 y reiniciá (paso 8).

---

## Contenido de este repositorio

```text
.
├── README.md                  (esta guía)
├── modulos_nuevos.tar.gz      (los seis módulos, listos para descomprimir)
├── .gitignore
└── modulos_propios/
    ├── health_admin_profiles/      (con tests/, README.md e INFORME.md)
    ├── health_user_person/         (con tests/ y README.md)
    ├── persona_datos_obligatorios/
    ├── persona_tipo_sangre/
    ├── persona_tipos_documento/
    └── persona_alta_ordenada/
```

Cada carpeta de módulo tiene su `tryton.cfg`. Dentro de `modulos_propios/` no
tiene que haber nada que no sea un módulo de Tryton.
