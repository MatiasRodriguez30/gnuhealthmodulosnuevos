from datetime import datetime

from trytond.exceptions import UserError
from trytond.model import ModelSQL, ModelView, Unique, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.wizard import Button, StateTransition, StateView, Wizard

__all__ = [
    'SpecialtyArea', 'SpecialtyAreaGroup', 'SpecialtyAreaSpecialty',
    'Specialty', 'HealthProfessional', 'ApplySpecialtyStart', 'ApplySpecialty']


class SpecialtyArea(ModelSQL, ModelView):
    'Área de especialidad'
    __name__ = 'gnuhealth.specialty.area'

    code = fields.Char('Código', required=True)
    name = fields.Char('Nombre', required=True)
    groups = fields.Many2Many(
        'gnuhealth.specialty.area-res.group', 'area', 'group',
        'Grupos por defecto')
    specialties = fields.Many2Many(
        'gnuhealth.specialty.area-specialty', 'area', 'specialty',
        'Especialidades')

    @classmethod
    def __setup__(cls):
        super().__setup__()
        t = cls.__table__()
        # El código del área no puede repetirse
        cls._sql_constraints += [
            ('code_uniq', Unique(t, t.code),
                'El código del área debe ser único.'),
            ]


class SpecialtyAreaGroup(ModelSQL):
    'Área de especialidad - Grupo'
    __name__ = 'gnuhealth.specialty.area-res.group'

    area = fields.Many2One(
        'gnuhealth.specialty.area', 'Área', required=True,
        ondelete='CASCADE')
    group = fields.Many2One(
        'res.group', 'Grupo', required=True, ondelete='CASCADE')

    @classmethod
    def __setup__(cls):
        super().__setup__()
        t = cls.__table__()
        cls._sql_constraints += [
            ('area_group_uniq', Unique(t, t.area, t.group),
                'El grupo ya está asignado a esta área.'),
            ]


class SpecialtyAreaSpecialty(ModelSQL):
    'Área de especialidad - Especialidad'
    __name__ = 'gnuhealth.specialty.area-specialty'

    area = fields.Many2One(
        'gnuhealth.specialty.area', 'Área', required=True,
        ondelete='CASCADE')
    specialty = fields.Many2One(
        'gnuhealth.specialty', 'Especialidad', required=True,
        ondelete='CASCADE')

    @classmethod
    def __setup__(cls):
        super().__setup__()
        t = cls.__table__()
        # Una especialidad solo puede estar en una área
        cls._sql_constraints += [
            ('specialty_uniq', Unique(t, t.specialty),
                'Cada especialidad puede pertenecer a una sola área.'),
            ]


class Specialty(metaclass=PoolMeta):
    __name__ = 'gnuhealth.specialty'

    area = fields.Function(
        fields.Many2One('gnuhealth.specialty.area', 'Área'), 'get_area')

    def get_area(self, name):
        # Área a la que pertenece la especialidad (si tiene)
        SpecialtyArea = Pool().get('gnuhealth.specialty.area')
        areas = SpecialtyArea.search(
            [('specialties', '=', self.id)], limit=1)
        return areas[0].id if areas else None


class HealthProfessional(metaclass=PoolMeta):
    __name__ = 'gnuhealth.healthprofessional'

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._buttons.update({'apply_specialty_permissions': {}})

    @classmethod
    @ModelView.button_action('health_admin_profiles.act_specialty_apply')
    def apply_specialty_permissions(cls, professionals):
        # El asistente hace el trabajo; este método solo abre la acción.
        pass


class ApplySpecialtyStart(ModelView):
    'Aplicar permisos por especialidad - Inicio'
    __name__ = 'gnuhealth.specialty.apply.start'

    professional = fields.Many2One(
        'gnuhealth.healthprofessional', 'Profesional', required=True,
        readonly=True)
    user = fields.Many2One('res.user', 'Usuario interno', readonly=True)
    areas = fields.Text('Áreas', readonly=True)
    groups = fields.Text('Grupos a otorgar', readonly=True)
    summary = fields.Text('Resumen', readonly=True)


class ApplySpecialty(Wizard):
    'Aplicar permisos por especialidad'
    __name__ = 'gnuhealth.specialty.apply'

    start = StateView(
        'gnuhealth.specialty.apply.start',
        'health_admin_profiles.specialty_apply_start_view', [
            Button('Cancelar', 'end', 'tryton-cancel'),
            Button('Aplicar', 'apply', 'tryton-ok', default=True),
            ])
    apply = StateTransition()

    def _compute(self, professional):
        # Calcula usuario, áreas y grupos según las especialidades
        SpecialtyArea = Pool().get('gnuhealth.specialty.area')
        user = None
        if professional.party:
            user = professional.party.internal_user
        area_names = []
        group_names = []
        group_ids = set()
        for hp in professional.specialties:
            if not hp.specialty:
                continue
            areas = SpecialtyArea.search(
                [('specialties', '=', hp.specialty.id)], limit=1)
            if not areas:
                continue
            area = areas[0]
            if area.name not in area_names:
                area_names.append(area.name)
            for group in area.groups:
                group_ids.add(group.id)
                if group.name not in group_names:
                    group_names.append(group.name)
        return user, area_names, group_names, group_ids

    def default_start(self, fields):
        Professional = Pool().get('gnuhealth.healthprofessional')
        active_id = Transaction().context.get('active_id')
        if not active_id:
            raise UserError('No se indicó el profesional.')
        professional = Professional(active_id)
        user, area_names, group_names, group_ids = self._compute(
            professional)
        if not area_names:
            resumen = (
                'El profesional no tiene especialidades con área asignada.')
        else:
            usuario = user.rec_name if user else '(sin usuario interno)'
            resumen = (
                f'Se agregarán {len(group_ids)} grupo(s) al usuario '
                f'{usuario}.')
        return {
            'professional': professional.id,
            'user': user.id if user else None,
            'areas': '\n'.join(sorted(area_names)) or 'Sin área asignada',
            'groups': '\n'.join(sorted(group_names))
            or 'Sin grupos por defecto',
            'summary': resumen,
            }

    def transition_apply(self):
        pool = Pool()
        User = pool.get('res.user')
        Log = pool.get('gnuhealth.admin.profile.log')

        professional = self.start.professional
        if not professional:
            raise UserError('No se indicó el profesional.')
        user, area_names, group_names, group_ids = self._compute(
            professional)
        if not user:
            raise UserError(
                'El profesional no tiene un usuario interno vinculado en su '
                'persona. Asignalo en la ficha de la persona (campo Usuario '
                'interno) y volvé a intentar.')
        current = {g.id for g in user.groups}
        add = sorted(group_ids - current)
        if add:
            User.write([user], {'groups': [('add', add)]})
        # Registro de auditoría: el log es de solo lectura para los usuarios,
        # así que lo escribe el servidor con el usuario 0.
        profile_id = user.admin_profile.id if user.admin_profile else None
        with Transaction().set_user(0):
            Log.create([{
                'date': datetime.now(),
                'user': user.id,
                'old_profile': profile_id,
                'new_profile': profile_id,
                'action': 'specialty',
                'groups_added': [('add', add)],
                'groups_removed': [('add', [])],
                }])
        return 'end'
