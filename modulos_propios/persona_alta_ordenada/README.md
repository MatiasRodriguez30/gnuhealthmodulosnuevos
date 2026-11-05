# Módulo: persona_alta_ordenada

## Objetivo

Unificar en un solo bloque llamado **Datos de alta** los dos grupos sueltos que
los módulos hermanos agregan al formulario de tercero (party.party) antes del
notebook:

- `grupo_datos_obligatorios` de `persona_datos_obligatorios`
  (email_principal, telefono_principal, domicilio_calle, domicilio_ciudad).
- `grupo_tipo_sangre` de `persona_tipo_sangre`
  (tipo_sangre, factor_rh).

El módulo es de **solo vistas**: no agrega campos ni modelos, únicamente una
vista heredada de `party.party_view_form`.

## Dependencias

```
ir
party
health
persona_datos_obligatorios
persona_tipos_documento
persona_tipo_sangre
```

## Antes y después

| Antes | Después |
|---|---|
| Grupo suelto "Datos obligatorios": email_principal, telefono_principal, domicilio_calle, domicilio_ciudad | Subgrupo **Contacto**: email_principal, telefono_principal |
| (mismo grupo) domicilio_calle, domicilio_ciudad | Subgrupo **Domicilio**: domicilio_calle (con `widget="char"`), domicilio_ciudad |
| Grupo suelto "Grupo sanguíneo": tipo_sangre, factor_rh | Subgrupo **Grupo sanguíneo**: tipo_sangre, factor_rh |
| Sin tipo ni número de documento en el alta | Subgrupo **Documento**: documento_tipo, documento_numero (los crea `persona_tipos_documento`) |
| Dos grupos separados antes del notebook | Un único bloque **Datos de alta** (col=6, colspan=6) con cuatro subgrupos de dos columnas antes del notebook |
| Resto del formulario sin cambios | Resto del formulario sin cambios |

### Ajustes de diseño

- **`yalign="0"` en cada subgrupo** (Documento, Contacto, Domicilio y Grupo
  sanguíneo): Tryton centra los subgrupos verticalmente por defecto, por lo que
  quedaban a distinta altura; con `yalign="0"` se alinean arriba (la vista base
  de Tryton usa el mismo atributo en su grupo `header`).
- **`widget="char"` en `domicilio_calle`**: el campo es de tipo `Text` y se veía
  como un cuadro de varias líneas; el widget `char` lo muestra como una línea
  simple (GNU Health hace lo mismo con `du_address`).

## Qué NO mueve y por qué

No se agregan ni se reposicionan `name`, `lastname`, `gender`, `dob`,
`marital_status` ni `identifiers`:

- `name` y `lastname` ya están en el grupo de cabecera: la vista de GNU Health
  `health.view_party_form` reemplaza el campo `name` de la vista base
  `party.party_view_form` por un grupo con `name` y `lastname`.
- `gender`, `dob`, `marital_status` (y otros datos clínicos) ya están en la
  página **Health** (`party_gnuhealth`) que agrega GNU Health.
- `identifiers` ya está en la página **Identifiers** de la vista base de Tryton.

Repetir cualquiera de esos campos en la vista produciría un campo duplicado,
que Tryton rechaza al aplicar la herencia.

## Técnica

La vista hereda `party.party_view_form` con `priority` 100 (se aplica después de
las vistas de `health`, `account`, `stock`, `purchase` y los módulos `persona_*`,
cuyo valor por defecto es 16). Los xpath:

1. Eliminan los dos grupos sueltos:
   - `group[@id='grupo_datos_obligatorios']` con `position="replace"` sin contenido (Tryton 7.0 no tiene la posición `remove`).
   - `group[@id='grupo_tipo_sangre']` con `position="replace"` sin contenido (Tryton 7.0 no tiene la posición `remove`).
2. Insertan antes de `notebook` el grupo `grupo_datos_alta` con los subgrupos
   `grupo_alta_documento`, `grupo_alta_contacto`, `grupo_alta_domicilio` y
   `grupo_alta_sangre` (todos con `yalign="0"`), que vuelven a declarar los
   mismos ocho campos.

## Mejora futura (versión 2)

Mover `gender`, `dob` y `marital_status` al bloque de alta. Eso requiere tocar
los grupos anidados de la página Health (`party_gnuhealth`) mediante xpath sobre
sus subgrupos, por lo que se deja para una versión posterior.

## QUÉ SE VERIFICÓ

- Ids de vista `party.party_view_form` (vista base de Tryton) y
  `health.view_party_form` (extensión de GNU Health) por lectura del código
  instalado el 04/11/2026.
- Nombres de campos (`documento_tipo`, `documento_numero`, `email_principal`,
  `telefono_principal`, `domicilio_calle`, `domicilio_ciudad`, `tipo_sangre`,
  `factor_rh`) y estructura de las vistas (grupos de cabecera, notebook, página
  Health, página Identifiers) por lectura del código instalado el 04/11/2026.
  `documento_tipo` y `documento_numero` los agrega `persona_tipos_documento`.
- Sintaxis de los XML con `xml.dom.minidom` y de los `.py` con `ast.parse`.
- Ningún `field` repetido en la vista y ninguna posición `remove` (solo `replace`).

## QUÉ NO SE VERIFICÓ

- No se vio el formulario renderizado en el cliente web (la vista combinada sí se comprobó con el motor de Tryton; ver abajo).
- No se corrieron las pruebas (`tests/__init__.py`).

## Pruebas

```bash
python -m trytond.tests.test_tryton persona_alta_ordenada
```

Pruebas incluidas (además de `test_view`, que ya trae `ModuleTestCase`):

- `test_vista_sin_campos_duplicados`: ningún `field` de la vista aparece dos veces.
- `test_vista_usa_solo_campos_existentes`: cada `field` y `label` existe en `party.party`.
- `test_vista_quita_grupos_hermanos`: hay xpath `replace` vacío para ambos grupos.
- `test_subgrupos_alineados_arriba`: los cuatro subgrupos existen con `yalign="0"` y `domicilio_calle` usa `widget="char"`.
- `test_registro_de_vista`: la vista hereda `party.party_view_form` y el archivo indicado por `name` existe en `view/`.

## Activación

Primera vez, enlazar el módulo (pide contraseña de root):

```bash
~/sync_modulos.sh
```

Luego, activar o actualizar en la base de pruebas:

```bash
trytond-admin -c /opt/gnuhealth/his-50/etc/trytond.conf -d bd_desarrollo -u persona_alta_ordenada --activate-dependencies
```

Después recargar la web (Ctrl+F5) y abrir **Terceros > Personas**.

## Autor

Proyecto GNU Health - Equipo 2026

## Verificación en bd_desarrollo (04/11/2026)

Activado en `bd_desarrollo` el 04/11/2026 con `trytond-admin -u ... --activate-dependencies` (estado `activated`). No se tocó `health50`.

Verificado con el motor real de Tryton (vista combinada de `party.party`, transacción de solo lectura):
- 67 campos en el formulario, ninguno repetido; `name`, `lastname`, `dob`, `gender`, `marital_status` e `identifiers` aparecen una vez.
- Los grupos sueltos `grupo_datos_obligatorios` y `grupo_tipo_sangre` ya no están; en su lugar existe `grupo_datos_alta`.

Corrección hecha al activar: la primera versión usaba `position="remove"`, que Tryton 7.0 rechaza (`Invalid attribute position for element xpath`). Se cambió por `replace` vacío.

**Ajuste de diseño posterior (04/11/2026):** se agregó `yalign="0"` a los subgrupos (alineación arriba), `widget="char"` en `domicilio_calle` y el subgrupo **Documento**. Este ajuste **todavía no se activó** en `bd_desarrollo` ni se vio renderizado: requiere `trytond-admin -u persona_alta_ordenada` y que `persona_tipos_documento` tenga los campos `documento_tipo` y `documento_numero`.

**No verificado:** las pruebas de `tests/__init__.py` no se corrieron con el runner de Tryton (no hay entorno de pruebas configurado), el formulario no se vio renderizado en el cliente web, y el servidor Tryton en ejecución necesita reinicio (lo hace Matías) para cargar el código Python nuevo.
