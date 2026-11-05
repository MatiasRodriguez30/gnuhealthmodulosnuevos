# SPDX-FileCopyrightText: 2026 Proyecto GNU Health
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.pool import Pool
from trytond.exceptions import UserError


class PersonaDatosObligatoriosTestCase(ModuleTestCase):
    "Pruebas unitarias para el módulo persona_datos_obligatorios"
    module = 'persona_datos_obligatorios'

    @with_transaction()
    def test_persona_sin_email_falla(self):
        """Verifica que intentar crear una persona sin email lance UserError."""
        pool = Pool()
        Party = pool.get('party.party')

        with self.assertRaises(UserError):
            Party.create([{
                'name': 'Juan',
                'lastname': 'Pérez',
                'is_person': True,
                'telefono_principal': '1122334455',
                'domicilio_calle': 'Av. Siempreviva 742',
                'domicilio_ciudad': 'Springfield',
            }])

    @with_transaction()
    def test_persona_completa_guarda(self):
        """Verifica que una persona con todos los datos requeridos se guarde correctamente."""
        pool = Pool()
        Party = pool.get('party.party')

        party, = Party.create([{
            'name': 'María',
            'lastname': 'Gómez',
            'is_person': True,
            'email_principal': 'maria.gomez@example.com',
            'telefono_principal': '1199887766',
            'domicilio_calle': 'Calle Falsa 123',
            'domicilio_ciudad': 'Buenos Aires',
        }])

        self.assertTrue(party.id)
        self.assertEqual(party.name, 'María')
        self.assertEqual(party.lastname, 'Gómez')
        self.assertEqual(party.email_principal, 'maria.gomez@example.com')
        self.assertEqual(party.telefono_principal, '1199887766')
        self.assertEqual(party.domicilio_calle, 'Calle Falsa 123')
        self.assertEqual(party.domicilio_ciudad, 'Buenos Aires')

        # Verificar que se crearon los registros correspondientes en contact_mechanism y address
        self.assertTrue(any(
            cm.type == 'email' and cm.value == 'maria.gomez@example.com'
            for cm in party.contact_mechanisms
        ))
        self.assertTrue(any(
            cm.type in ('phone', 'mobile') and cm.value == '1199887766'
            for cm in party.contact_mechanisms
        ))
        self.assertTrue(any(
            addr.street == 'Calle Falsa 123' and addr.city == 'Buenos Aires'
            for addr in party.addresses
        ))

    @with_transaction()
    def test_institucion_no_afectada(self):
        """Verifica que una institución pueda guardarse sin los datos exigidos a personas."""
        pool = Pool()
        Party = pool.get('party.party')

        institucion, = Party.create([{
            'name': 'Hospital de Clínicas',
            'is_institution': True,
            'is_person': False,
        }])

        self.assertTrue(institucion.id)
        self.assertEqual(institucion.name, 'Hospital de Clínicas')
        self.assertTrue(institucion.is_institution)
        self.assertFalse(institucion.is_person)

    @with_transaction()
    def test_persona_sin_telefono_falla(self):
        """Verifica que una persona sin teléfono lance UserError."""
        pool = Pool()
        Party = pool.get('party.party')

        with self.assertRaises(UserError):
            Party.create([{
                'name': 'Carlos',
                'lastname': 'López',
                'is_person': True,
                'email_principal': 'carlos.lopez@example.com',
                'domicilio_calle': 'Av. Corrientes 1000',
            }])

    @with_transaction()
    def test_persona_sin_domicilio_falla(self):
        """Verifica que una persona sin calle en domicilio lance UserError."""
        pool = Pool()
        Party = pool.get('party.party')

        with self.assertRaises(UserError):
            Party.create([{
                'name': 'Ana',
                'lastname': 'Martínez',
                'is_person': True,
                'email_principal': 'ana.martinez@example.com',
                'telefono_principal': '1144556677',
            }])

    @with_transaction()
    def test_persona_sin_apellido_falla(self):
        """Verifica que una persona sin apellido lance UserError."""
        pool = Pool()
        Party = pool.get('party.party')

        with self.assertRaises(UserError):
            Party.create([{
                'name': 'Pedro',
                'is_person': True,
                'email_principal': 'pedro@example.com',
                'telefono_principal': '1133221100',
                'domicilio_calle': 'Belgrano 456',
            }])

    @with_transaction()
    def test_tercero_no_persona_no_afectado(self):
        """Verifica que un tercero que no es persona (empresa) no sea afectado por la validación."""
        pool = Pool()
        Party = pool.get('party.party')

        empresa, = Party.create([{
            'name': 'Distribuidora Médica S.A.',
            'is_person': False,
        }])

        self.assertTrue(empresa.id)
        self.assertEqual(empresa.name, 'Distribuidora Médica S.A.')

    @with_transaction()
    def test_edicion_de_persona_existente_no_se_revalida(self):
        """Una persona ya existente sin datos de contacto se puede seguir editando."""
        pool = Pool()
        Party = pool.get('party.party')

        # Se crea como no-persona (no se valida) y luego se la marca como persona,
        # simulando un registro preexistente incompleto.
        party, = Party.create([{
            'name': 'Registro Legado',
            'is_person': False,
        }])
        Party.write([party], {'is_person': True})
        Party.write([party], {'name': 'Registro Legado Editado'})

        self.assertEqual(party.name, 'Registro Legado Editado')


del ModuleTestCase


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        PersonaDatosObligatoriosTestCase))
    return suite
