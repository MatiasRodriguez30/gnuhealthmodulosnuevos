# SPDX-FileCopyrightText: 2026 Proyecto GNU Health
# SPDX-License-Identifier: GPL-3.0-or-later

import re
from trytond.i18n import gettext
from trytond.model import fields
from trytond.pool import PoolMeta

try:
    from trytond.modules.party.exceptions import InvalidIdentifierCode
except ImportError:
    from trytond.exceptions import UserError

    class InvalidIdentifierCode(UserError):
        pass


class Identifier(metaclass=PoolMeta):
    """
    Extensión del modelo party.identifier para incorporar nuevos tipos de
    documentos de identidad argentinos e internacionales, con sus respectivas
    reglas de validación.
    """
    __name__ = 'party.identifier'

    # Tipos adicionales de documentos con sus etiquetas en español.
    # El core solo ofrece los tipos habilitados en la configuración de
    # Terceros (en bd_desarrollo no estaban habilitados ar_dni ni ar_cuit),
    # por eso se garantizan acá. Si luego se habilitan en la configuración,
    # get_types() no los duplica porque deduplica por clave.
    EXTRA_TYPES = [
        ('ar_dni', 'DNI'),
        ('ar_cuit', 'CUIT'),
        ('ar_le', 'Libreta de Enrolamiento'),
        ('ar_lc', 'Libreta Cívica'),
        ('ar_cuil', 'CUIL'),
        ('passport', 'Pasaporte'),
        ('ar_ci', 'Cédula de Identidad'),
    ]

    @classmethod
    def get_types(cls):
        """
        Extiende la lista de selección de tipos de identificadores sumando
        los nuevos tipos definidos sin duplicar ni modificar el core.
        """
        types = list(super().get_types() or [])
        existing_keys = {code for code, _ in types if code is not None}
        for code, label in cls.EXTRA_TYPES:
            if code not in existing_keys:
                types.append((code, label))
        return types

    @classmethod
    def _is_valid_le_lc(cls, code):
        """
        Valida Libreta de Enrolamiento (LE) y Libreta Cívica (LC).
        Formato requerido: 6 a 8 dígitos numéricos (se admiten puntos o espacios
        de formateo habituales).
        """
        if not code:
            return False
        clean = re.sub(r'[\s.]', '', str(code))
        return bool(re.fullmatch(r'\d{6,8}', clean))

    @classmethod
    def _is_valid_cuil(cls, code):
        """
        Valida Código Único de Identificación Laboral (CUIL).
        Formato requerido: 11 dígitos numéricos con el mismo dígito verificador
        que el CUIT (algoritmo módulo 11 de AFIP/ANSES).
        """
        if not code:
            return False
        clean = re.sub(r'[-\s.]', '', str(code))
        if not re.fullmatch(r'\d{11}', clean):
            return False

        # Si python-stdnum tiene disponible stdnum.ar.cuit, validamos con la librería
        try:
            from stdnum.ar import cuit
            return bool(cuit.is_valid(clean))
        except (ImportError, AttributeError):
            pass

        # Algoritmo autónomo de cálculo de dígito verificador (módulo 11)
        weights = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
        check = sum(w * int(n) for w, n in zip(weights, clean[:10])) % 11
        expected = '012345678990'[11 - check]
        return clean[10] == expected

    @classmethod
    def _is_valid_passport_ci(cls, code):
        """
        Valida Pasaporte y Cédula de Identidad (CI).
        Formato requerido: alfanumérico de 5 a 20 caracteres.
        """
        if not code:
            return False
        clean = str(code).strip()
        return bool(re.fullmatch(r'[a-zA-Z0-9]{5,20}', clean))

    @fields.depends('type', 'party', 'code')
    def check_code(self):
        """
        Valida el código del identificador según su tipo.
        Los tipos nuevos usan validaciones de formato específicas.
        Para el resto de tipos se invoca la validación del core, evitando que
        tipos no conocidos por python-stdnum rompan la ejecución.
        """
        if not self.code or not self.type:
            return

        is_valid = True
        if self.type in ('ar_le', 'ar_lc'):
            is_valid = self._is_valid_le_lc(self.code)
        elif self.type == 'ar_cuil':
            is_valid = self._is_valid_cuil(self.code)
        elif self.type in ('passport', 'ar_ci'):
            is_valid = self._is_valid_passport_ci(self.code)
        else:
            try:
                super().check_code()
            except (AttributeError, ImportError):
                # Tipos no soportados o desconocidos por python-stdnum no deben romper
                pass
            return

        if not is_valid:
            party_name = ''
            if self.party and getattr(self.party, 'id', None) and self.party.id > 0:
                party_name = getattr(self.party, 'rec_name', '') or ''
            type_label = getattr(self, 'type_string', None) or self.type
            raise InvalidIdentifierCode(
                gettext(
                    'party.msg_invalid_code',
                    type=type_label,
                    code=self.code,
                    party=party_name))
