# SPDX-FileCopyrightText: 2026 Proyecto GNU Health
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import unittest
import xml.etree.ElementTree as ET

import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.pool import Pool


# Ruta de la carpeta del módulo (el archivo está en tests/__init__.py)
MODULE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEW_FILE = os.path.join(MODULE_DIR, 'view', 'party_form.xml')
PARTY_XML_FILE = os.path.join(MODULE_DIR, 'party.xml')


def _cargar_vista():
    """Devuelve el árbol XML de la vista heredada de este módulo."""
    return ET.parse(VIEW_FILE).getroot()


class PersonaAltaOrdenadaTestCase(ModuleTestCase):
    """Pruebas unitarias para el módulo persona_alta_ordenada."""
    module = 'persona_alta_ordenada'

    def test_vista_sin_campos_duplicados(self):
        """Verifica que ningún campo aparece dos veces en la vista del módulo."""
        raiz = _cargar_vista()
        nombres = [
            nodo.get('name')
            for nodo in raiz.iter('field')
            if nodo.get('name')
        ]
        repetidos = sorted({n for n in nombres if nombres.count(n) > 1})
        self.assertEqual(
            repetidos, [],
            f"Campos repetidos en la vista: {repetidos}")

    @with_transaction()
    def test_vista_usa_solo_campos_existentes(self):
        """Verifica que cada field y label de la vista existe en party.party."""
        pool = Pool()
        Party = pool.get('party.party')
        raiz = _cargar_vista()
        faltantes = []
        for etiqueta in ('field', 'label'):
            for nodo in raiz.iter(etiqueta):
                nombre = nodo.get('name')
                if nombre and nombre not in Party._fields:
                    faltantes.append(nombre)
        self.assertEqual(
            faltantes, [],
            f"Campos inexistentes en party.party: {faltantes}")

    def test_vista_quita_grupos_hermanos(self):
        """Verifica que la vista quita los grupos de los módulos hermanos."""
        raiz = _cargar_vista()
        removidas = [
            nodo.get('expr', '')
            for nodo in raiz.iter('xpath')
            if nodo.get('position') == 'replace' and len(nodo) == 0
        ]
        self.assertTrue(
            any('grupo_datos_obligatorios' in expr for expr in removidas),
            f"Falta el remove de grupo_datos_obligatorios: {removidas}")
        self.assertTrue(
            any('grupo_tipo_sangre' in expr for expr in removidas),
            f"Falta el remove de grupo_tipo_sangre: {removidas}")

    def test_subgrupos_alineados_arriba(self):
        """Verifica la alineación arriba de los subgrupos y el widget char."""
        raiz = _cargar_vista()
        grupos = {
            nodo.get('id'): nodo
            for nodo in raiz.iter('group')
            if nodo.get('id')
        }
        for id_grupo in ('grupo_alta_documento', 'grupo_alta_contacto',
                'grupo_alta_domicilio', 'grupo_alta_sangre'):
            self.assertIn(id_grupo, grupos, f"Falta el subgrupo {id_grupo}")
            self.assertEqual(
                grupos[id_grupo].get('yalign'), '0',
                f"El subgrupo {id_grupo} no tiene yalign 0")
        # domicilio_calle es un campo Text: se muestra con el widget char
        calle = [
            nodo for nodo in grupos['grupo_alta_domicilio'].iter('field')
            if nodo.get('name') == 'domicilio_calle'
        ]
        self.assertEqual(len(calle), 1, "Falta el field domicilio_calle")
        self.assertEqual(
            calle[0].get('widget'), 'char',
            "domicilio_calle no usa el widget char")

    def test_registro_de_vista(self):
        """Verifica la herencia de la vista y que el archivo de vista exista."""
        raiz = ET.parse(PARTY_XML_FILE).getroot()
        registros = [
            nodo for nodo in raiz.iter('record')
            if nodo.get('model') == 'ir.ui.view'
        ]
        self.assertEqual(len(registros), 1, "Debe haber un solo registro de vista")
        registro = registros[0]
        campos = {
            campo.get('name'): campo
            for campo in registro.findall('field')
        }
        self.assertIn('inherit', campos, "El registro no declara inherit")
        self.assertEqual(
            campos['inherit'].get('ref'), 'party.party_view_form')
        self.assertIn('name', campos, "El registro no declara la vista")
        archivo = os.path.join(
            MODULE_DIR, 'view', campos['name'].text.strip() + '.xml')
        self.assertTrue(
            os.path.isfile(archivo),
            f"No existe el archivo de vista {archivo}")


del ModuleTestCase


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        PersonaAltaOrdenadaTestCase))
    return suite
