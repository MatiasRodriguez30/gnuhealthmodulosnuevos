# SPDX-FileCopyrightText: 2026 Proyecto GNU Health
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.pool import Pool
from trytond.exceptions import UserError

try:
    from trytond.modules.party.exceptions import InvalidIdentifierCode
except ImportError:
    class InvalidIdentifierCode(UserError):
        pass


class PersonaTiposDocumentoTestCase(ModuleTestCase):
    """
    Pruebas unitarias para el módulo persona_tipos_documento.
    Verifica:
    - Registro de los nuevos tipos de documento ('ar_le', 'ar_lc', 'ar_cuil', 'passport', 'ar_ci').
    - Validación de códigos válidos e inválidos para cada nuevo tipo.
    - Conservación del funcionamiento de tipos preexistentes ('ar_dni', 'ar_cuit').
    - Estabilidad de check_code ante tipos no reconocidos por python-stdnum.
    """
    module = 'persona_tipos_documento'

    # -------------------------------------------------------------------------
    # Pruebas de lógica pura de validación (métodos auxiliares)
    # -------------------------------------------------------------------------

    def test_validador_le_lc_auxiliar(self):
        """Verifica la lógica de formato para Libreta de Enrolamiento y Cívica (6 a 8 dígitos)."""
        pool = Pool()
        Identifier = pool.get('party.identifier')

        # Códigos válidos
        self.assertTrue(Identifier._is_valid_le_lc('123456'))
        self.assertTrue(Identifier._is_valid_le_lc('1234567'))
        self.assertTrue(Identifier._is_valid_le_lc('12345678'))
        self.assertTrue(Identifier._is_valid_le_lc('12.345.678'))
        self.assertTrue(Identifier._is_valid_le_lc('1.234.567'))
        self.assertTrue(Identifier._is_valid_le_lc(' 12345678 '))

        # Códigos inválidos
        self.assertFalse(Identifier._is_valid_le_lc('12345'))       # 5 dígitos (menor a 6)
        self.assertFalse(Identifier._is_valid_le_lc('123456789'))   # 9 dígitos (mayor a 8)
        self.assertFalse(Identifier._is_valid_le_lc('12345A'))      # Letras
        self.assertFalse(Identifier._is_valid_le_lc('ABCDEF'))      # Letras
        self.assertFalse(Identifier._is_valid_le_lc(''))            # Vacío
        self.assertFalse(Identifier._is_valid_le_lc(None))          # None

    def test_validador_cuil_auxiliar(self):
        """Verifica la lógica de formato y dígito verificador módulo 11 para CUIL (11 dígitos)."""
        pool = Pool()
        Identifier = pool.get('party.identifier')

        # Códigos válidos con checksum CUIT/CUIL correcto
        self.assertTrue(Identifier._is_valid_cuil('20-05536168-2'))
        self.assertTrue(Identifier._is_valid_cuil('20055361682'))
        self.assertTrue(Identifier._is_valid_cuil('27-28564123-9'))
        self.assertTrue(Identifier._is_valid_cuil('27285641239'))
        self.assertTrue(Identifier._is_valid_cuil('20-30123456-4'))

        # Códigos inválidos
        self.assertFalse(Identifier._is_valid_cuil('20-05536168-3'))  # Dígito verificador erróneo
        self.assertFalse(Identifier._is_valid_cuil('20055361683'))    # Dígito verificador erróneo
        self.assertFalse(Identifier._is_valid_cuil('1234567890'))     # 10 dígitos
        self.assertFalse(Identifier._is_valid_cuil('200553616821'))   # 12 dígitos
        self.assertFalse(Identifier._is_valid_cuil('2005536168A'))    # Carácter alfabético
        self.assertFalse(Identifier._is_valid_cuil(''))               # Vacío
        self.assertFalse(Identifier._is_valid_cuil(None))             # None

    def test_validador_passport_ci_auxiliar(self):
        """Verifica la lógica alfanumérica de 5 a 20 caracteres para Pasaporte y Cédula."""
        pool = Pool()
        Identifier = pool.get('party.identifier')

        # Códigos válidos
        self.assertTrue(Identifier._is_valid_passport_ci('A12345678'))
        self.assertTrue(Identifier._is_valid_passport_ci('PASSPORT123'))
        self.assertTrue(Identifier._is_valid_passport_ci('CI123456'))
        self.assertTrue(Identifier._is_valid_passport_ci('12345'))                 # Longitud 5 (mínima)
        self.assertTrue(Identifier._is_valid_passport_ci('A1234567890123456789'))  # Longitud 20 (máxima)
        self.assertTrue(Identifier._is_valid_passport_ci(' ABCDE '))              # Con espacios exteriores

        # Códigos inválidos
        self.assertFalse(Identifier._is_valid_passport_ci('1234'))                 # 4 caracteres (menor a 5)
        self.assertFalse(Identifier._is_valid_passport_ci('123456789012345678901'))# 21 caracteres (mayor a 20)
        self.assertFalse(Identifier._is_valid_passport_ci('PASS-123'))             # Contiene guion
        self.assertFalse(Identifier._is_valid_passport_ci('PASS 123'))             # Contiene espacio interno
        self.assertFalse(Identifier._is_valid_passport_ci('!@#$%'))                # Símbolos no alfanuméricos
        self.assertFalse(Identifier._is_valid_passport_ci(''))                     # Vacío
        self.assertFalse(Identifier._is_valid_passport_ci(None))                   # None

    # -------------------------------------------------------------------------
    # Pruebas transaccionales en el entorno de Tryton
    # -------------------------------------------------------------------------

    @with_transaction()
    def test_get_types_incluye_nuevos_tipos(self):
        """Verifica que Identifier.get_types() incluya los 5 nuevos tipos y preserve los existentes."""
        pool = Pool()
        Identifier = pool.get('party.identifier')

        types_dict = dict(Identifier.get_types())

        # Verificar nuevos tipos agregados con sus etiquetas en español
        self.assertIn('ar_le', types_dict)
        self.assertEqual(types_dict['ar_le'], 'Libreta de Enrolamiento')

        self.assertIn('ar_lc', types_dict)
        self.assertEqual(types_dict['ar_lc'], 'Libreta Cívica')

        self.assertIn('ar_cuil', types_dict)
        self.assertEqual(types_dict['ar_cuil'], 'CUIL')

        self.assertIn('passport', types_dict)
        self.assertEqual(types_dict['passport'], 'Pasaporte')

        self.assertIn('ar_ci', types_dict)
        self.assertEqual(types_dict['ar_ci'], 'Cédula de Identidad')

        # Verificar que se preserven los tipos core preexistentes
        self.assertIn('ar_dni', types_dict)
        self.assertIn('ar_cuit', types_dict)

    @with_transaction()
    def test_le_valida_y_rechaza(self):
        """Verifica que Libreta de Enrolamiento guarde con código válido y falle con inválido."""
        pool = Pool()
        Party = pool.get('party.party')
        Identifier = pool.get('party.identifier')

        party, = Party.create([{'name': 'Persona Test LE', 'is_person': False}])

        # Válido: 8 dígitos
        ident, = Identifier.create([{
            'party': party.id,
            'type': 'ar_le',
            'code': '12345678',
        }])
        self.assertTrue(ident.id)
        self.assertEqual(ident.type, 'ar_le')
        self.assertEqual(ident.code, '12345678')

        # Inválido: 5 dígitos (debe fallar)
        with self.assertRaises((UserError, InvalidIdentifierCode)):
            Identifier.create([{
                'party': party.id,
                'type': 'ar_le',
                'code': '12345',
            }])

        # Inválido: caracteres alfabéticos (debe fallar)
        with self.assertRaises((UserError, InvalidIdentifierCode)):
            Identifier.create([{
                'party': party.id,
                'type': 'ar_le',
                'code': '12345A',
            }])

    @with_transaction()
    def test_lc_valida_y_rechaza(self):
        """Verifica que Libreta Cívica guarde con código válido y falle con inválido."""
        pool = Pool()
        Party = pool.get('party.party')
        Identifier = pool.get('party.identifier')

        party, = Party.create([{'name': 'Persona Test LC', 'is_person': False}])

        # Válido: 7 dígitos con puntos
        ident, = Identifier.create([{
            'party': party.id,
            'type': 'ar_lc',
            'code': '1.234.567',
        }])
        self.assertTrue(ident.id)
        self.assertEqual(ident.type, 'ar_lc')

        # Inválido: menor a 6 dígitos
        with self.assertRaises((UserError, InvalidIdentifierCode)):
            Identifier.create([{
                'party': party.id,
                'type': 'ar_lc',
                'code': '123',
            }])

    @with_transaction()
    def test_cuil_valida_y_rechaza(self):
        """Verifica que CUIL guarde con dígito verificador correcto y rechace erróneo."""
        pool = Pool()
        Party = pool.get('party.party')
        Identifier = pool.get('party.identifier')

        party, = Party.create([{'name': 'Persona Test CUIL', 'is_person': False}])

        # Válido: CUIL con dígito verificador correcto (20-05536168-2)
        ident, = Identifier.create([{
            'party': party.id,
            'type': 'ar_cuil',
            'code': '20-05536168-2',
        }])
        self.assertTrue(ident.id)
        self.assertEqual(ident.type, 'ar_cuil')

        # Inválido: dígito verificador incorrecto (20-05536168-3)
        with self.assertRaises((UserError, InvalidIdentifierCode)):
            Identifier.create([{
                'party': party.id,
                'type': 'ar_cuil',
                'code': '20-05536168-3',
            }])

        # Inválido: longitud incorrecta (10 dígitos)
        with self.assertRaises((UserError, InvalidIdentifierCode)):
            Identifier.create([{
                'party': party.id,
                'type': 'ar_cuil',
                'code': '2005536168',
            }])

    @with_transaction()
    def test_passport_valida_y_rechaza(self):
        """Verifica que Pasaporte guarde con formato alfanumérico (5-20) y falle si no cumple."""
        pool = Pool()
        Party = pool.get('party.party')
        Identifier = pool.get('party.identifier')

        party, = Party.create([{'name': 'Persona Test Passport', 'is_person': False}])

        # Válido: alfanumérico entre 5 y 20 caracteres
        ident, = Identifier.create([{
            'party': party.id,
            'type': 'passport',
            'code': 'PASSPORT123',
        }])
        self.assertTrue(ident.id)
        self.assertEqual(ident.type, 'passport')

        # Inválido: menor a 5 caracteres
        with self.assertRaises((UserError, InvalidIdentifierCode)):
            Identifier.create([{
                'party': party.id,
                'type': 'passport',
                'code': 'AB12',
            }])

        # Inválido: contiene caracteres no alfanuméricos
        with self.assertRaises((UserError, InvalidIdentifierCode)):
            Identifier.create([{
                'party': party.id,
                'type': 'passport',
                'code': 'PASS-1234!',
            }])

    @with_transaction()
    def test_ci_valida_y_rechaza(self):
        """Verifica que Cédula de Identidad guarde con formato alfanumérico (5-20) y falle si no cumple."""
        pool = Pool()
        Party = pool.get('party.party')
        Identifier = pool.get('party.identifier')

        party, = Party.create([{'name': 'Persona Test CI', 'is_person': False}])

        # Válido: 8 caracteres alfanuméricos
        ident, = Identifier.create([{
            'party': party.id,
            'type': 'ar_ci',
            'code': 'CI123456',
        }])
        self.assertTrue(ident.id)
        self.assertEqual(ident.type, 'ar_ci')

        # Inválido: 3 caracteres (menor a 5)
        with self.assertRaises((UserError, InvalidIdentifierCode)):
            Identifier.create([{
                'party': party.id,
                'type': 'ar_ci',
                'code': '123',
            }])

    @with_transaction()
    def test_dni_sigue_funcionando(self):
        """Verifica que el tipo preexistente DNI ('ar_dni') continúe validando correctamente."""
        pool = Pool()
        Party = pool.get('party.party')
        Identifier = pool.get('party.identifier')

        party, = Party.create([{'name': 'Persona Test DNI', 'is_person': False}])

        # DNI válido
        ident, = Identifier.create([{
            'party': party.id,
            'type': 'ar_dni',
            'code': '12345678',
        }])
        self.assertTrue(ident.id)
        self.assertEqual(ident.type, 'ar_dni')

        # DNI inválido (demasiado corto o letras)
        with self.assertRaises((UserError, InvalidIdentifierCode)):
            Identifier.create([{
                'party': party.id,
                'type': 'ar_dni',
                'code': '123',
            }])

    @with_transaction()
    def test_cuit_sigue_funcionando(self):
        """Verifica que el tipo preexistente CUIT ('ar_cuit') continúe validando correctamente."""
        pool = Pool()
        Party = pool.get('party.party')
        Identifier = pool.get('party.identifier')

        party, = Party.create([{'name': 'Persona Test CUIT', 'is_person': False}])

        # CUIT válido
        ident, = Identifier.create([{
            'party': party.id,
            'type': 'ar_cuit',
            'code': '20-05536168-2',
        }])
        self.assertTrue(ident.id)
        self.assertEqual(ident.type, 'ar_cuit')

        # CUIT inválido (dígito verificador incorrecto)
        with self.assertRaises((UserError, InvalidIdentifierCode)):
            Identifier.create([{
                'party': party.id,
                'type': 'ar_cuit',
                'code': '20-05536168-3',
            }])

    @with_transaction()
    def test_check_code_directo(self):
        """Verifica la invocación directa del método check_code sobre instancias de Identifier."""
        pool = Pool()
        Party = pool.get('party.party')
        Identifier = pool.get('party.identifier')

        party, = Party.create([{'name': 'Persona Test Directo', 'is_person': False}])

        # Instancia con LE válida: check_code() no debe lanzar excepción
        ident_valido = Identifier(party=party, type='ar_le', code='12345678')
        ident_valido.check_code()

        # Instancia con LE inválida: check_code() debe lanzar excepción
        ident_invalido = Identifier(party=party, type='ar_le', code='99')
        with self.assertRaises((UserError, InvalidIdentifierCode)):
            ident_invalido.check_code()

    # -------------------------------------------------------------------------
    # Pruebas de carga rápida del documento (documento_tipo / documento_numero)
    # -------------------------------------------------------------------------

    @with_transaction()
    def test_crear_persona_con_documento(self):
        """Al crear con tipo y número de documento se genera un party.identifier y se lee igual."""
        pool = Pool()
        Party = pool.get('party.party')
        Identifier = pool.get('party.identifier')

        party, = Party.create([{
            'name': 'Persona Test Documento',
            'is_person': False,
            'documento_tipo': 'ar_dni',
            'documento_numero': '12345678',
        }])

        identifiers = Identifier.search([('party', '=', party.id)])
        self.assertEqual(len(identifiers), 1)
        self.assertEqual(identifiers[0].type, 'ar_dni')
        self.assertEqual(identifiers[0].code, '12345678')

        # Al releer la persona desde la base devuelven los mismos valores
        party = Party(party.id)
        self.assertEqual(party.documento_tipo, 'ar_dni')
        self.assertEqual(party.documento_numero, '12345678')

    @with_transaction()
    def test_escribir_solo_tipo_documento(self):
        """Escribir solo documento_tipo cambia el type del identificador existente sin crear otro."""
        pool = Pool()
        Party = pool.get('party.party')
        Identifier = pool.get('party.identifier')

        party, = Party.create([{
            'name': 'Persona Test Tipo Solo',
            'is_person': False,
            'documento_tipo': 'ar_dni',
            'documento_numero': '12345678',
        }])

        Party.write([party], {'documento_tipo': 'ar_le'})

        identifiers = Identifier.search([('party', '=', party.id)])
        self.assertEqual(len(identifiers), 1)
        self.assertEqual(identifiers[0].type, 'ar_le')
        self.assertEqual(identifiers[0].code, '12345678')

        party = Party(party.id)
        self.assertEqual(party.documento_tipo, 'ar_le')
        self.assertEqual(party.documento_numero, '12345678')

    @with_transaction()
    def test_crear_numero_sin_tipo_falla(self):
        """Crear con documento_numero pero sin documento_tipo lanza UserError."""
        pool = Pool()
        Party = pool.get('party.party')

        with self.assertRaises(UserError):
            Party.create([{
                'name': 'Persona Test Numero Solo',
                'is_person': False,
                'documento_numero': '12345678',
            }])

    @with_transaction()
    def test_crear_documento_invalido_falla(self):
        """Crear con tipo y número inválido lo rechaza la validación de party.identifier."""
        pool = Pool()
        Party = pool.get('party.party')

        with self.assertRaises(UserError):
            Party.create([{
                'name': 'Persona Test Documento Invalido',
                'is_person': False,
                'documento_tipo': 'ar_dni',
                'documento_numero': '123',
            }])

    @with_transaction()
    def test_crear_sin_documento_no_crea_identificadores(self):
        """Crear una persona sin datos de documento no crea ningún identificador."""
        pool = Pool()
        Party = pool.get('party.party')
        Identifier = pool.get('party.identifier')

        party, = Party.create([{
            'name': 'Persona Test Sin Documento',
            'is_person': False,
        }])

        identifiers = Identifier.search([('party', '=', party.id)])
        self.assertEqual(len(identifiers), 0)

        party = Party(party.id)
        self.assertFalse(party.documento_tipo)
        self.assertFalse(party.documento_numero)

    @with_transaction()
    def test_campos_documento_son_editables(self):
        """Los campos de carga rápida no deben ser de solo lectura en el cliente."""
        pool = Pool()
        Party = pool.get('party.party')
        definicion = Party.fields_get(['documento_tipo', 'documento_numero'])
        for nombre in ('documento_tipo', 'documento_numero'):
            self.assertFalse(
                definicion[nombre].get('readonly'),
                "%s no debe ser de solo lectura" % nombre)


del ModuleTestCase


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        PersonaTiposDocumentoTestCase))
    return suite
