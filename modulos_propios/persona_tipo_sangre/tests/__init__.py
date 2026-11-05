# SPDX-FileCopyrightText: 2026 Proyecto GNU Health
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.pool import Pool


class PersonaTipoSangreTestCase(ModuleTestCase):
    "Pruebas unitarias para el módulo persona_tipo_sangre"
    module = 'persona_tipo_sangre'

    @with_transaction()
    def test_guardar_y_leer_tipo_sangre_persona(self):
        """Verifica que se guarden y lean correctamente grupo sanguíneo y factor Rh en party.party."""
        pool = Pool()
        Party = pool.get('party.party')

        party, = Party.create([{
            'name': 'Juan',
            'lastname': 'Pérez',
            'is_person': True,
            'tipo_sangre': 'A',
            'factor_rh': '+',
        }])

        self.assertTrue(party.id)
        self.assertEqual(party.tipo_sangre, 'A')
        self.assertEqual(party.factor_rh, '+')
        self.assertEqual(party.sangre_resumen, 'A +')

    @with_transaction()
    def test_sangre_resumen_variantes(self):
        """Verifica el cálculo del campo funcional sangre_resumen en distintas combinaciones."""
        pool = Pool()
        Party = pool.get('party.party')

        p_o_neg, = Party.create([{
            'name': 'Carlos',
            'lastname': 'López',
            'is_person': True,
            'tipo_sangre': 'O',
            'factor_rh': '-',
        }])
        self.assertEqual(p_o_neg.sangre_resumen, 'O -')

        p_solo_grupo, = Party.create([{
            'name': 'Ana',
            'lastname': 'Gómez',
            'is_person': True,
            'tipo_sangre': 'B',
        }])
        self.assertEqual(p_solo_grupo.sangre_resumen, 'B')

        p_solo_factor, = Party.create([{
            'name': 'Luis',
            'lastname': 'Martínez',
            'is_person': True,
            'factor_rh': '+',
        }])
        self.assertEqual(p_solo_factor.sangre_resumen, '+')

        p_vacio, = Party.create([{
            'name': 'Elena',
            'lastname': 'Ruiz',
            'is_person': True,
        }])
        self.assertIsNone(p_vacio.sangre_resumen)

    @with_transaction()
    def test_sincronizacion_paciente_campos_vacios(self):
        """Verifica que al guardar una persona con paciente asociado y campos vacíos, el paciente reciba los valores."""
        pool = Pool()
        Party = pool.get('party.party')
        Patient = pool.get('gnuhealth.patient')

        party, = Party.create([{
            'name': 'María',
            'lastname': 'Fernández',
            'is_person': True,
        }])

        # Crear el paciente asociado con grupo y factor vacíos
        patient, = Patient.create([{
            'party': party.id,
            'blood_type': None,
            'rh': None,
        }])
        self.assertIsNone(patient.blood_type)
        self.assertIsNone(patient.rh)

        # Actualizar la persona con grupo y factor
        Party.write([party], {
            'tipo_sangre': 'B',
            'factor_rh': '+',
        })

        # Recargar el paciente y verificar que recibió los datos de la persona
        patient = Patient(patient.id)
        self.assertEqual(patient.blood_type, 'B')
        self.assertEqual(patient.rh, '+')

    @with_transaction()
    def test_sincronizacion_paciente_con_valor_existente_no_se_pisa(self):
        """Verifica que NUNCA se pise un dato clínico existente en el paciente (no se sobreescribe)."""
        pool = Pool()
        Party = pool.get('party.party')
        Patient = pool.get('gnuhealth.patient')

        party, = Party.create([{
            'name': 'Roberto',
            'lastname': 'Díaz',
            'is_person': True,
            'tipo_sangre': 'O',
            'factor_rh': '+',
        }])

        # Paciente ya registrado previamente con datos clínicos distintos (ej: AB-)
        patient, = Patient.create([{
            'party': party.id,
            'blood_type': 'AB',
            'rh': '-',
        }])

        # Intentar modificar el tipo de sangre en la persona
        Party.write([party], {
            'tipo_sangre': 'A',
            'factor_rh': '+',
        })

        # Verificar que la persona tiene los nuevos datos
        party = Party(party.id)
        self.assertEqual(party.tipo_sangre, 'A')
        self.assertEqual(party.factor_rh, '+')

        # Verificar que el paciente MANTIENE intactos sus datos clínicos originales
        patient = Patient(patient.id)
        self.assertEqual(patient.blood_type, 'AB')
        self.assertEqual(patient.rh, '-')

    @with_transaction()
    def test_sincronizacion_parcial_paciente(self):
        """Verifica que si el paciente tiene solo uno de los campos vacío, se copie solo el vacío sin alterar el otro."""
        pool = Pool()
        Party = pool.get('party.party')
        Patient = pool.get('gnuhealth.patient')

        party, = Party.create([{
            'name': 'Sofía',
            'lastname': 'Castro',
            'is_person': True,
        }])

        # Paciente con blood_type ya cargado ('A'), pero sin rh
        patient, = Patient.create([{
            'party': party.id,
            'blood_type': 'A',
            'rh': None,
        }])

        # Guardar en la persona un grupo distinto ('O') y un factor ('+')
        Party.write([party], {
            'tipo_sangre': 'O',
            'factor_rh': '+',
        })

        # El paciente debe conservar su blood_type 'A' y recibir únicamente el factor '+' que estaba vacío
        patient = Patient(patient.id)
        self.assertEqual(patient.blood_type, 'A')
        self.assertEqual(patient.rh, '+')

    @with_transaction()
    def test_persona_sin_paciente_no_falla(self):
        """Verifica que una persona sin registro de paciente asociado se guarde sin errores."""
        pool = Pool()
        Party = pool.get('party.party')

        party, = Party.create([{
            'name': 'Federico',
            'lastname': 'Molina',
            'is_person': True,
            'tipo_sangre': 'AB',
            'factor_rh': '-',
        }])
        self.assertTrue(party.id)
        self.assertEqual(party.tipo_sangre, 'AB')
        self.assertEqual(party.factor_rh, '-')

        Party.write([party], {
            'tipo_sangre': 'O',
        })
        party = Party(party.id)
        self.assertEqual(party.tipo_sangre, 'O')
        self.assertEqual(party.factor_rh, '-')


del ModuleTestCase


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        PersonaTipoSangreTestCase))
    return suite
