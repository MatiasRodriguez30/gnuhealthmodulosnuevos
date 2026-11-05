import unittest

import trytond.tests.test_tryton
from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction


class HealthUserPersonTestCase(ModuleTestCase):
    'Pruebas del módulo health_user_person'
    module = 'health_user_person'

    @with_transaction()
    def test_vincular_buscar_y_desvincular_persona(self):
        pool = Pool()
        User = pool.get('res.user')
        Party = pool.get('party.party')
        user, = User.create([{'name': 'Prueba', 'login': 'prueba_persona',
                    'password': 'testpassword'}])
        persona, = Party.create([{'name': 'Ana', 'lastname': 'Pérez',
                    'is_person': True, 'gender': 'f', 'fed_country': None}])
        User.write([user], {'person': persona.id})
        self.assertEqual(User(user.id).person, persona)
        self.assertEqual(User.search([('person', '=', persona.id)]), [user])
        User.write([user], {'person': None})
        self.assertIsNone(User(user.id).person)
        self.assertIn(user, User.search([('person', '=', None)]))


del ModuleTestCase


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            HealthUserPersonTestCase))
    return suite
