# SPDX-FileCopyrightText: 2026 Proyecto GNU Health
# SPDX-License-Identifier: GPL-3.0-or-later

from trytond.model import fields
from trytond.pool import Pool, PoolMeta

# Opciones válidas para grupo sanguíneo (sistema ABO) y factor Rh
TIPO_SANGRE_SELECTION = [
    (None, ''),
    ('A', 'A'),
    ('B', 'B'),
    ('AB', 'AB'),
    ('O', 'O'),
]

FACTOR_RH_SELECTION = [
    (None, ''),
    ('+', '+'),
    ('-', '-'),
]


class Party(metaclass=PoolMeta):
    """
    Extensión del modelo party.party para registrar grupo sanguíneo y factor Rh
    directamente sobre la persona, con sincronización segura hacia el paciente
    clínico (gnuhealth.patient).
    """
    __name__ = 'party.party'

    tipo_sangre = fields.Selection(
        TIPO_SANGRE_SELECTION,
        'Grupo sanguíneo',
        sort=False,
        help='Grupo sanguíneo del sistema ABO (A, B, AB, O).')

    factor_rh = fields.Selection(
        FACTOR_RH_SELECTION,
        'Factor Rh',
        sort=False,
        help='Factor Rhesus (+ o -).')

    sangre_resumen = fields.Function(
        fields.Char(
            'Resumen grupo y factor',
            readonly=True,
            help='Resumen legible del grupo sanguíneo y factor Rh (ej. "A +").'),
        'get_sangre_resumen')

    def get_sangre_resumen(self, name):
        """
        Devuelve un resumen textual de solo lectura con el grupo y factor Rh
        (por ejemplo, 'A +', 'O -', 'B'). Devuelve None si no hay datos cargados.
        """
        parts = []
        if self.tipo_sangre:
            parts.append(self.tipo_sangre)
        if self.factor_rh:
            parts.append(self.factor_rh)
        return ' '.join(parts) if parts else None

    @classmethod
    def create(cls, vlist):
        parties = super().create(vlist)
        cls._sync_blood_type_to_patient(parties)
        return parties

    @classmethod
    def write(cls, *args):
        super().write(*args)
        party_ids = set()
        actions = iter(args)
        for records, values in zip(actions, actions):
            for r in records:
                if getattr(r, 'id', None):
                    party_ids.add(r.id)
        if party_ids:
            cls._sync_blood_type_to_patient(cls.browse(list(party_ids)))

    @classmethod
    def _sync_blood_type_to_patient(cls, parties):
        """
        Sincroniza de forma segura el tipo de sangre y factor Rh hacia el
        registro de paciente (gnuhealth.patient) asociado a cada persona:
        - Aplica únicamente si la persona ya cuenta con un registro en gnuhealth.patient.
        - Si el paciente tiene blood_type o rh VACÍOS, se le copia el valor de la persona.
        - NUNCA se pisa un dato clínico que el paciente ya tenga cargado previamente.
        - Si ambos tienen valores distintos cargados, no se modifica el paciente
          para salvaguardar la integridad de la historia clínica.
        """
        pool = Pool()
        try:
            Patient = pool.get('gnuhealth.patient')
        except KeyError:
            return

        candidate_parties = [
            p for p in parties
            if getattr(p, 'id', None) and (p.tipo_sangre or p.factor_rh)
        ]
        if not candidate_parties:
            return

        party_map = {p.id: p for p in candidate_parties}
        patients = Patient.search([
            ('party', 'in', list(party_map.keys())),
        ])

        to_update = []
        for patient in patients:
            party_id = patient.party.id if patient.party else None
            party = party_map.get(party_id)
            if not party:
                continue

            to_write = {}
            # Copiar blood_type solo si el paciente lo tiene vacío
            if party.tipo_sangre and not patient.blood_type:
                to_write['blood_type'] = party.tipo_sangre

            # Copiar rh solo si el paciente lo tiene vacío
            if party.factor_rh and not patient.rh:
                to_write['rh'] = party.factor_rh

            if to_write:
                to_update.extend([[patient], to_write])

        if to_update:
            Patient.write(*to_update)
