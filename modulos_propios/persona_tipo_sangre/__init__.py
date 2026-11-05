# SPDX-FileCopyrightText: 2026 Proyecto GNU Health
# SPDX-License-Identifier: GPL-3.0-or-later

from trytond.pool import Pool
from . import party


def register():
    Pool.register(
        party.Party,
        module='persona_tipo_sangre', type_='model')
