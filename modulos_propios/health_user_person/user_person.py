from trytond.exceptions import UserError
from trytond.model import fields
from trytond.pool import Pool, PoolMeta


class User(metaclass=PoolMeta):
    __name__ = 'res.user'

    person = fields.Function(
        fields.Many2One(
            'party.party', 'Persona',
            domain=[('is_person', '=', True)]),
        'get_person', setter='set_person', searcher='search_person')

    def get_person(self, name):
        Party = Pool().get('party.party')
        parties = Party.search([('internal_user', '=', self.id)], limit=1)
        return parties[0].id if parties else None

    @classmethod
    def set_person(cls, users, name, value):
        Party = Pool().get('party.party')
        user_ids = [u.id for u in users]
        current = {
            p.internal_user.id: p
            for p in Party.search([('internal_user', 'in', user_ids)])
            }
        party = Party(value) if value else None
        if party:
            if not party.is_person:
                raise UserError('El registro elegido no es una persona.')
            if (party.internal_user
                    and party.internal_user.id not in user_ids):
                raise UserError(
                    'La persona ya está vinculada a otro usuario.')
        for user in users:
            old = current.get(user.id)
            if party:
                if old and old.id != party.id:
                    Party.write([old], {'internal_user': None})
                if not party.internal_user or party.internal_user.id != user.id:
                    Party.write([party], {'internal_user': user.id})
            elif old:
                Party.write([old], {'internal_user': None})

    @classmethod
    def search_person(cls, name, clause):
        Party = Pool().get('party.party')
        _, operator, operand = clause
        if operand is None and operator in ('=', '!='):
            # Usuarios sin persona vinculada (=) o con persona (!=)
            con_persona = [p.internal_user.id for p in Party.search([
                        ('internal_user', '!=', None),
                        ])]
            return [('id', 'not in' if operator == '=' else 'in',
                    con_persona)]
        if operator in ('=', 'in'):
            ids = operand if operator == 'in' else (
                [operand] if operand else [])
            parties = Party.search([
                    ('id', 'in', ids),
                    ('internal_user', '!=', None),
                    ])
            return [('id', 'in', [p.internal_user.id for p in parties])]
        if operator in ('!=', 'not in'):
            ids = operand if operator == 'not in' else (
                [operand] if operand else [])
            parties = Party.search([
                    ('id', 'in', ids),
                    ('internal_user', '!=', None),
                    ])
            return [('id', 'not in', [p.internal_user.id for p in parties])]
        if operator in ('ilike', 'not ilike'):
            parties = Party.search([
                    ('rec_name', operator, operand),
                    ('internal_user', '!=', None),
                    ])
            users = [p.internal_user.id for p in parties]
            return [('id', 'in' if operator == 'ilike' else 'not in', users)]
        return [('id', 'in', [])]
