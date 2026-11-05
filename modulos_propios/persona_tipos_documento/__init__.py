# SPDX-FileCopyrightText: 2026 Proyecto GNU Health
# SPDX-License-Identifier: GPL-3.0-or-later

from trytond.pool import Pool
from . import identifier
from . import party


def register():
    Pool.register(
        identifier.Identifier,
        party.Party,
        module='persona_tipos_documento', type_='model')
