from datetime import datetime

from trytond.exceptions import UserError
from trytond.model import ModelSQL, ModelView, Unique, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.wizard import Button, StateTransition, StateView, Wizard

__all__ = [
    'AdminProfile', 'AdminProfileGroup', 'AdminProfileLogGroupAdded',
    'AdminProfileLogGroupRemoved', 'AdminProfileLog', 'AdminProfileUserGroup',
    'User', 'ApplyProfileStart', 'ApplyProfile']

# Modelos cuyos registros base (cargados por XML) el administrador debe poder
# editar desde la interfaz: perfiles, áreas y sus relaciones.
MODELOS_EDITABLES = [
    'gnuhealth.admin.profile',
    'gnuhealth.admin.profile-res.group',
    'gnuhealth.specialty.area',
    'gnuhealth.specialty.area-res.group',
    'gnuhealth.specialty.area-specialty',
    ]


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

    @classmethod
    def __register__(cls, module_name):
        super().__register__(module_name)
        # Migración: versiones anteriores cargaban perfiles y áreas sin
        # noupdate y Tryton los bloqueaba como "configuración base", así que
        # ni el administrador podía editarlos. Ahora los XML usan
        # noupdate="1"; acá se marcan como editables los registros que ya
        # estaban cargados (Tryton no actualiza esa marca por sí solo).
        # Solo toca los datos de este módulo.
        ModelData = Pool().get('ir.model.data')
        model_data = ModelData.__table__()
        cursor = Transaction().connection.cursor()
        cursor.execute(*model_data.update(
                [model_data.noupdate], [True],
                where=(model_data.module == module_name)
                & model_data.model.in_(MODELOS_EDITABLES)))


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


class AdminProfileUserGroup(ModelSQL):
    'Usuario - Grupo otorgado por el perfil'
    __name__ = 'gnuhealth.admin.profile.user-res.group'

    user = fields.Many2One(
        'res.user', 'Usuario', required=True, ondelete='CASCADE')
    group = fields.Many2One(
        'res.group', 'Grupo', required=True, ondelete='CASCADE')


class User(metaclass=PoolMeta):
    __name__ = 'res.user'

    admin_profile = fields.Many2One(
        'gnuhealth.admin.profile', 'Perfil de puesto', ondelete='SET NULL')
    profile_groups = fields.Many2Many(
        'gnuhealth.admin.profile.user-res.group', 'user', 'group',
        'Grupos otorgados por el perfil', readonly=True,
        help='Grupos que el perfil le otorgó al usuario la última vez que se '
        'aplicó. Sirven para saber qué quitar al cambiar o sincronizar el '
        'perfil sin tocar los grupos agregados a mano.')
    extra_groups = fields.Function(
        fields.Many2Many('res.user-res.group', 'user', 'group',
            'Grupos extra'),
        'get_extra_groups')

    def _grupos_otorgados(self, profile):
        # Grupos que el perfil le dio a este usuario. Si el usuario recibió
        # el perfil con una versión anterior del módulo (sin ese registro),
        # se toman los grupos actuales del perfil que el usuario tiene.
        if self.profile_groups:
            return {g.id for g in self.profile_groups}
        if profile:
            current = {g.id for g in self.groups}
            return {g.id for g in profile.groups} & current
        return set()

    def get_extra_groups(self, name):
        # Grupos del usuario que no vienen del perfil asignado
        current = {g.id for g in self.groups}
        return sorted(current - self._grupos_otorgados(self.admin_profile))

    @fields.depends('admin_profile', 'groups', 'profile_groups')
    def on_change_admin_profile(self):
        # Vista previa en el formulario: apenas se elige el perfil se ven los
        # grupos que va a tener el usuario. Al guardar, create() y write()
        # vuelven a hacer el mismo cálculo en el servidor.
        Group = Pool().get('res.group')
        current = {g.id for g in (self.groups or [])}
        if self.profile_groups:
            otorgados = {g.id for g in self.profile_groups}
        elif self.id is not None and self.id >= 0:
            # Usuario ya guardado: se usa lo que le había dado su perfil
            # anterior (incluye a los asignados con la versión anterior).
            guardado = self.__class__(self.id)
            otorgados = guardado._grupos_otorgados(guardado.admin_profile)
        else:
            otorgados = set()
        new_groups = ({g.id for g in self.admin_profile.groups}
            if self.admin_profile else set())
        target = (current - otorgados) | new_groups
        self.groups = Group.browse(sorted(target))
        self.profile_groups = Group.browse(sorted(new_groups))
        self.extra_groups = Group.browse(sorted(target - new_groups))

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
    def _apply_profile(cls, user, old_profile, new_profile, action,
            registrar_sin_cambios=True):
        current = {g.id for g in user.groups}
        otorgados = user._grupos_otorgados(old_profile)
        new_groups = ({g.id for g in new_profile.groups}
            if new_profile else set())
        # Regla del proyecto: se quitan los grupos que había dado el perfil
        # anterior, se agregan los del nuevo y se conservan los agregados a
        # mano.
        target = (current - otorgados) | new_groups
        remove = sorted(current - target)
        add = sorted(target - current)
        # Se escribe solo la diferencia: quitar y agregar el mismo grupo en
        # una sola escritura (perfiles que comparten grupos) lo perdería.
        registrados = {g.id for g in user.profile_groups}
        values = {'profile_groups': [
                ('remove', sorted(registrados - new_groups)),
                ('add', sorted(new_groups - registrados)),
                ]}
        if remove or add:
            values['groups'] = [('remove', remove), ('add', add)]
        # No incluye 'admin_profile', así que no hay recursión
        cls.write([user], values)
        if remove or add or registrar_sin_cambios:
            cls._log_change(
                user, old_profile, new_profile, action, add, remove)
        return bool(remove or add)

    @classmethod
    def create(cls, vlist):
        users = super().create(vlist)
        for user in users:
            user = cls(user.id)
            if user.admin_profile:
                cls._apply_profile(user, None, user.admin_profile, 'create')
        return users

    @classmethod
    def write(cls, *args):
        pool = Pool()
        AdminProfile = pool.get('gnuhealth.admin.profile')
        # Se guarda el perfil anterior de los usuarios de TODOS los pares
        # (usuarios, valores) que cambian admin_profile.
        actions = iter(args)
        anteriores = {}
        for users, values in zip(actions, actions):
            if 'admin_profile' in values:
                for user in users:
                    anteriores.setdefault(
                        user.id,
                        user.admin_profile.id if user.admin_profile else None)
        result = super().write(*args)
        for user_id, old_id in anteriores.items():
            user = cls(user_id)
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
            cls._apply_profile(user, old_profile, user.admin_profile, action)
        return result

    @classmethod
    def apply_profile_to_users(cls, users, profile, action='apply'):
        # Sincroniza: agrega los grupos nuevos del perfil y quita los que se
        # sacaron del perfil, sin tocar los grupos agregados a mano. Solo
        # deja registro en el log de los usuarios que cambiaron.
        count = 0
        for user in users:
            user = cls(user.id)
            if cls._apply_profile(user, profile, profile, action,
                    registrar_sin_cambios=False):
                count += 1
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
                f'con el perfil {profile.name}: se agregan los grupos '
                'nuevos del perfil y se quitan los que se sacaron de él. '
                'Los grupos agregados a mano no se tocan.'),
            }

    def transition_apply(self):
        User = Pool().get('res.user')
        profile = self.start.profile
        if not profile:
            raise UserError('No se indicó el perfil.')
        users = User.search([('admin_profile', '=', profile.id)])
        User.apply_profile_to_users(users, profile, 'apply')
        return 'end'
