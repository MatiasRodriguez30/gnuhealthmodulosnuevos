from trytond.pool import Pool
from . import user_person


def register():
    Pool.register(
        user_person.User,
        module='health_user_person', type_='model')
