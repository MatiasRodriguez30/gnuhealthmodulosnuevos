import unittest

import trytond.tests.test_tryton
from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction


class HealthAdminProfilesTestCase(ModuleTestCase):
    'Pruebas del módulo health_admin_profiles'
    module = 'health_admin_profiles'

    def _usuario(self, login, **valores):
        User = Pool().get('res.user')
        datos = {'name': login, 'login': login, 'password': 'testpassword'}
        datos.update(valores)
        user, = User.create([datos])
        return user

    def _grupos(self, user):
        User = Pool().get('res.user')
        return {g.id for g in User(user.id).groups}

    @with_transaction()
    def test_cambio_y_quita_de_perfil_conservan_grupos_manuales(self):
        pool = Pool()
        User = pool.get('res.user')
        Profile = pool.get('gnuhealth.admin.profile')
        ModelData = pool.get('ir.model.data')
        recepcion, = Profile.search([('code', '=', 'RECEPCION')])
        medico, = Profile.search([('code', '=', 'MEDICO')])
        manual = ModelData.get_id('account', 'group_account')
        user = self._usuario('prueba_perfil', admin_profile=recepcion.id,
            groups=[('add', [manual])])
        self.assertEqual(self._grupos(user),
            {g.id for g in recepcion.groups} | {manual})
        User.write([user], {'admin_profile': medico.id})
        self.assertEqual(self._grupos(user),
            {g.id for g in medico.groups} | {manual})
        User.write([user], {'admin_profile': None})
        self.assertEqual(self._grupos(user), {manual})

    @with_transaction()
    def test_aplicar_a_usuarios_quita_grupos_sacados_del_perfil(self):
        pool = Pool()
        User = pool.get('res.user')
        Profile = pool.get('gnuhealth.admin.profile')
        ModelData = pool.get('ir.model.data')
        g1 = ModelData.get_id('health', 'group_health_frontdesk')
        g2 = ModelData.get_id('party', 'group_party_admin')
        manual = ModelData.get_id('account', 'group_account')
        perfil, = Profile.create([{'code': 'PRUEBA', 'name': 'Prueba',
                    'groups': [('add', [g1, g2])]}])
        user = self._usuario('prueba_sync', admin_profile=perfil.id,
            groups=[('add', [manual])])
        Profile.write([perfil], {'groups': [('remove', [g2])]})
        User.apply_profile_to_users([user], perfil)
        self.assertEqual(self._grupos(user), {g1, manual})

    @with_transaction()
    def test_cambio_entre_perfiles_que_comparten_un_grupo(self):
        pool = Pool()
        User = pool.get('res.user')
        Profile = pool.get('gnuhealth.admin.profile')
        ModelData = pool.get('ir.model.data')
        comun = ModelData.get_id('health', 'group_health_frontdesk')
        g_a = ModelData.get_id('party', 'group_party_admin')
        g_b = ModelData.get_id('health', 'group_health_back_office')
        perfil_a, perfil_b = Profile.create([
                {'code': 'PRUEBA_A', 'name': 'A',
                    'groups': [('add', [comun, g_a])]},
                {'code': 'PRUEBA_B', 'name': 'B',
                    'groups': [('add', [comun, g_b])]},
                ])
        user = self._usuario('prueba_comparten', admin_profile=perfil_a.id)
        User.write([user], {'admin_profile': perfil_b.id})
        self.assertEqual(self._grupos(user), {comun, g_b})
        self.assertEqual(
            {g.id for g in User(user.id).profile_groups}, {comun, g_b})

    @with_transaction()
    def test_write_con_varios_pares_aplica_todos_los_perfiles(self):
        pool = Pool()
        User = pool.get('res.user')
        Profile = pool.get('gnuhealth.admin.profile')
        recepcion, = Profile.search([('code', '=', 'RECEPCION')])
        medico, = Profile.search([('code', '=', 'MEDICO')])
        u1 = self._usuario('prueba_par_1')
        u2 = self._usuario('prueba_par_2')
        User.write([u1], {'admin_profile': recepcion.id},
            [u2], {'admin_profile': medico.id})
        self.assertTrue(
            {g.id for g in recepcion.groups} <= self._grupos(u1))
        self.assertTrue({g.id for g in medico.groups} <= self._grupos(u2))

    @with_transaction()
    def test_perfiles_y_areas_base_son_editables(self):
        pool = Pool()
        Profile = pool.get('gnuhealth.admin.profile')
        Area = pool.get('gnuhealth.specialty.area')
        recepcion, = Profile.search([('code', '=', 'RECEPCION')])
        Profile.write([recepcion], {'name': 'Recepción editada',
                'groups': [('remove', [recepcion.groups[0].id])]})
        area = Area.search([], limit=1)[0]
        Area.write([area], {'name': 'Área editada'})


del ModuleTestCase


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            HealthAdminProfilesTestCase))
    return suite
