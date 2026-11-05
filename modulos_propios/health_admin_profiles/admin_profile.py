from datetime import datetime

from trytond.exceptions import UserError
from trytond.model import ModelSQL, ModelView, Unique, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.wizard import Button, StateTransition, StateView, Wizard

__all__ = [
    'AdminProfile', 'AdminProfileGroup', 'AdminProfileLogGroupAdded',
    'AdminProfileLogGroupRemoved', 'AdminProfileLog', 'User',
    'ApplyProfileStart', 'ApplyProfile']


class AdminProfile(ModelSQL, ModelView):
    'Perfil de puesto'
    __name__ = 'gnuhealth.admin.profile'

    code = fields.Char('Código', required=True)
    name = fields.Char('Nombre', required=True)
    category = fields.Char('Categoría')
    description = fields.Text('Descripción')
    active = fields.Boolean('Activo')
    groups = fields.Many2Many(
        'gnuhealth.admin.profile-res.group', 'profile', 'group', 'Grupos')

    @staticmethod
    def default_active():
        return True

    @classmethod
    @ModelView.button_action('health_admin_profiles.act_admin_profile_apply')
    def apply_to_users(cls, profiles):
        # El asistente hace el trabajo; este método solo abre la acción.
        pass

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._buttons.update({'apply_to_users': {}})
        t = cls.__table__()
        cls._sql_constraints += [
            ('code_uniq', Unique(t, t.code),
                'El código del perfil debe ser único.'),
            ]


class AdminProfileGroup(ModelSQL):
    'Perfil de puesto - Grupo'
    __name__ = 'gnuhealth.admin.profile-res.group'

    profile = fields.Many2One(
        'gnuhealth.admin.profile', 'Perfil', required=True,
        ondelete='CASCADE')
    group = fields.Many2One(
        'res.group', 'Grupo', required=True, ondelete='CASCADE')

    @classmethod
    def __setup__(cls):
        super().__setup__()
        t = cls.__table__()
        cls._sql_constraints += [
            ('profile_group_uniq', Unique(t, t.profile, t.group),
                'El grupo ya está asignado al perfil.'),
            ]


class AdminProfileLogGroupAdded(ModelSQL):
    'Log de perfil - Grupo agregado'
    __name__ = 'gnuhealth.admin.profile.log-res.group.added'

    log = fields.Many2One(
        'gnuhealth.admin.profile.log', 'Log', required=True,
        ondelete='CASCADE')
    group = fields.Many2One(
        'res.group', 'Grupo', required=True, ondelete='CASCADE')


class AdminProfileLogGroupRemoved(ModelSQL):
    'Log de perfil - Grupo quitado'
    __name__ = 'gnuhealth.admin.profile.log-res.group.removed'

    log = fields.Many2One(
        'gnuhealth.admin.profile.log', 'Log', required=True,
        ondelete='CASCADE')
    group = fields.Many2One(
        'res.group', 'Grupo', required=True, ondelete='CASCADE')


class AdminProfileLog(ModelSQL, ModelView):
    'Log de cambios de perfil'
    __name__ = 'gnuhealth.admin.profile.log'

    date = fields.DateTime('Fecha', required=True)
    user = fields.Many2One(
        'res.user', 'Usuario afectado', required=True, ondelete='CASCADE')
    old_profile = fields.Many2One(
        'gnuhealth.admin.profile', 'Perfil anterior', ondelete='SET NULL')
    new_profile = fields.Many2One(
        'gnuhealth.admin.profile', 'Perfil nuevo', ondelete='SET NULL')
    action = fields.Selection([
            ('create', 'Alta de usuario'),
            ('assign', 'Asignación de perfil'),
            ('change', 'Cambio de perfil'),
            ('remove', 'Quita de perfil'),
            ('apply', 'Aplicación masiva'),
            ('specialty', 'Permisos por especialidad'),
            ], 'Acción', required=True)
    groups_added = fields.Many2Many(
        'gnuhealth.admin.profile.log-res.group.added', 'log', 'group',
        'Grupos agregados')
    groups_removed = fields.Many2Many(
        'gnuhealth.admin.profile.log-res.group.removed', 'log', 'group',
        'Grupos quitados')

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._order.insert(0, ('date', 'DESC'))


class User(metaclass=PoolMeta):
    __name__ = 'res.user'

    admin_profile = fields.Many2One(
        'gnuhealth.admin.profile', 'Perfil de puesto', ondelete='SET NULL')
    extra_groups = fields.Function(
        fields.Many2Many('res.user-res.group', 'user', 'group',
            'Grupos extra'),
        'get_extra_groups')

    def get_extra_groups(self, name):
        # Grupos del usuario que no pertenecen al perfil asignado
        current = {g.id for g in self.groups}
        if not self.admin_profile:
            return sorted(current)
        profile_groups = {g.id for g in self.admin_profile.groups}
        return sorted(current - profile_groups)

    @classmethod
    def _log_change(cls, user, old_profile, new_profile, action, added,
            removed):
        Log = Pool().get('gnuhealth.admin.profile.log')
        # El log es de solo lectura para los usuarios: lo escribe el servidor
        # con el usuario 0 para no depender de los permisos del que dispara.
        with Transaction().set_user(0):
            Log.create([{
                        'date': datetime.now(),
                        'user': user.id,
                        'old_profile': old_profile.id if old_profile else None,
                        'new_profile': new_profile.id if new_profile else None,
                        'action': action,
                        'groups_added': [('add', added)],
                        'groups_removed': [('add', removed)],
                        }])

    @classmethod
    def _apply_profile(cls, user, old_profile, new_profile, action):
        current = {g.id for g in user.groups}
        old_groups = ({g.id for g in old_profile.groups}
            if old_profile else set())
        new_groups = ({g.id for g in new_profile.groups}
            if new_profile else set())
        # Regla del proyecto: se conservan los grupos extra del usuario
        target = (current - old_groups) | new_groups
        remove = sorted(current - target)
        add = sorted(target - current)
        if remove or add:
            # No incluye 'admin_profile', así que no hay recursión
            cls.write([user], {
                    'groups': [('remove', remove), ('add', add)],
                    })
        cls._log_change(user, old_profile, new_profile, action, add, remove)

    @classmethod
    def create(cls, vlist):
        users = super().create(vlist)
        for user in users:
            if user.admin_profile:
                user = cls(user.id)
                cls._apply_profile(user, None, user.admin_profile, 'create')
        return users

    @classmethod
    def write(cls, users, values, *args):
        pool = Pool()
        AdminProfile = pool.get('gnuhealth.admin.profile')
        old_profiles = {
            u.id: (u.admin_profile.id if u.admin_profile else None)
            for u in users}
        result = super().write(users, values, *args)
        if 'admin_profile' in values:
            for user in users:
                user = cls(user.id)
                old_id = old_profiles.get(user.id)
                new_id = user.admin_profile.id if user.admin_profile else None
                if old_id == new_id:
                    continue
                old_profile = AdminProfile(old_id) if old_id else None
                if old_id is None:
                    action = 'assign'
                elif new_id is None:
                    action = 'remove'
                else:
                    action = 'change'
                cls._apply_profile(
                    user, old_profile, user.admin_profile, action)
        return result

    @classmethod
    def apply_profile_to_users(cls, users, profile, action='apply'):
        profile_groups = {g.id for g in profile.groups}
        count = 0
        for user in users:
            current = {g.id for g in user.groups}
            target = current | profile_groups
            add = sorted(target - current)
            if add:
                cls.write([user], {'groups': [('add', add)]})
                count += 1
            cls._log_change(user, user.admin_profile, profile, action, add, [])
        return count


class ApplyProfileStart(ModelView):
    'Aplicar perfil - Inicio'
    __name__ = 'gnuhealth.admin.profile.apply.start'

    profile = fields.Many2One(
        'gnuhealth.admin.profile', 'Perfil', required=True, readonly=True)
    summary = fields.Text('Resumen', readonly=True)


class ApplyProfile(Wizard):
    'Aplicar perfil'
    __name__ = 'gnuhealth.admin.profile.apply'

    start = StateView('gnuhealth.admin.profile.apply.start',
        'health_admin_profiles.admin_profile_apply_start_view', [
            Button('Cancelar', 'end', 'tryton-cancel'),
            Button('Aplicar', 'apply', 'tryton-ok', default=True),
            ])
    apply = StateTransition()

    def default_start(self, fields):
        pool = Pool()
        AdminProfile = pool.get('gnuhealth.admin.profile')
        User = pool.get('res.user')
        active_id = Transaction().context.get('active_id')
        if not active_id:
            raise UserError('No se indicó el perfil.')
        profile = AdminProfile(active_id)
        users = User.search([('admin_profile', '=', profile.id)])
        return {
            'profile': profile.id,
            'summary': (f'Se van a sincronizar {len(users)} usuario(s) '
                f'con el perfil {profile.name}.'),
            }

    def transition_apply(self):
        User = Pool().get('res.user')
        profile = self.start.profile
        if not profile:
            raise UserError('No se indicó el perfil.')
        users = User.search([('admin_profile', '=', profile.id)])
        User.apply_profile_to_users(users, profile, 'apply')
        return 'end'
