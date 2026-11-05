# SPDX-FileCopyrightText: 2026 Proyecto GNU Health
# SPDX-License-Identifier: GPL-3.0-or-later

from trytond.pool import Pool


def register():
    # Módulo de solo vistas: no registra modelos ni asistentes.
    # La vista heredada se declara en party.xml.
    pass
