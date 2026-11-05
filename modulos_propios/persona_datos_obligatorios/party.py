# SPDX-FileCopyrightText: 2026 Proyecto GNU Health
# SPDX-License-Identifier: GPL-3.0-or-later

from trytond.exceptions import UserError
from trytond.i18n import gettext
from trytond.model import fields
from trytond.pool import Pool, PoolMeta


class Party(metaclass=PoolMeta):
    __name__ = 'party.party'

    email_principal = fields.Function(
        fields.Char('Email Principal'),
        'get_email_principal', setter='set_email_principal')
    telefono_principal = fields.Function(
        fields.Char('Teléfono Principal'),
        'get_telefono_principal', setter='set_telefono_principal')
    domicilio_calle = fields.Function(
        fields.Text('Calle'),
        'get_domicilio_calle', setter='set_domicilio_calle')
    domicilio_ciudad = fields.Function(
        fields.Char('Ciudad'),
        'get_domicilio_ciudad', setter='set_domicilio_ciudad')

    def get_email_principal(self, name):
        """Devuelve el valor del primer contact mechanism de tipo email."""
        for cm in (self.contact_mechanisms or ()):
            if cm.type == 'email':
                return cm.value
        return None

    def get_telefono_principal(self, name):
        """Devuelve el valor del primer contact mechanism de tipo phone o mobile."""
        for cm in (self.contact_mechanisms or ()):
            if cm.type in ('phone', 'mobile'):
                return cm.value
        return None

    def get_domicilio_calle(self, name):
        """Devuelve la calle de la primera dirección."""
        if self.addresses:
            return self.addresses[0].street
        return None

    def get_domicilio_ciudad(self, name):
        """Devuelve la ciudad de la primera dirección."""
        if self.addresses:
            return self.addresses[0].city
        return None

    @classmethod
    def _find_contact_mechanism(cls, party, types):
        pool = Pool()
        ContactMechanism = pool.get('party.contact_mechanism')
        if party.id and party.id > 0:
            mechanisms = ContactMechanism.search([
                ('party', '=', party.id),
                ('type', 'in', list(types)),
            ], order=[('sequence', 'ASC'), ('id', 'ASC')], limit=1)
            if mechanisms:
                return mechanisms[0]
        for cm in (party.contact_mechanisms or ()):
            if cm.type in types:
                return cm
        return None

    @classmethod
    def set_email_principal(cls, parties, name, value):
        """Crea o actualiza el primer contact mechanism de tipo email."""
        pool = Pool()
        ContactMechanism = pool.get('party.contact_mechanism')
        to_save = []
        to_create = []
        for party in parties:
            cm = cls._find_contact_mechanism(party, ('email',))
            if cm:
                if value is not None:
                    cm.value = value
                    to_save.append(cm)
            elif value:
                to_create.append({
                    'party': party.id,
                    'type': 'email',
                    'value': value,
                })
        if to_save:
            ContactMechanism.save(to_save)
        if to_create:
            ContactMechanism.create(to_create)

    @classmethod
    def set_telefono_principal(cls, parties, name, value):
        """Crea o actualiza el primer contact mechanism de tipo phone o mobile."""
        pool = Pool()
        ContactMechanism = pool.get('party.contact_mechanism')
        to_save = []
        to_create = []
        for party in parties:
            cm = cls._find_contact_mechanism(party, ('phone', 'mobile'))
            if cm:
                if value is not None:
                    cm.value = value
                    to_save.append(cm)
            elif value:
                to_create.append({
                    'party': party.id,
                    'type': 'phone',
                    'value': value,
                })
        if to_save:
            ContactMechanism.save(to_save)
        if to_create:
            ContactMechanism.create(to_create)

    @classmethod
    def _find_address(cls, party):
        pool = Pool()
        Address = pool.get('party.address')
        if party.id and party.id > 0:
            addresses = Address.search([
                ('party', '=', party.id),
            ], order=[('sequence', 'ASC'), ('id', 'ASC')], limit=1)
            if addresses:
                return addresses[0]
        if party.addresses:
            return party.addresses[0]
        return None

    @classmethod
    def set_domicilio_calle(cls, parties, name, value):
        """Crea o actualiza la calle de la primera dirección."""
        pool = Pool()
        Address = pool.get('party.address')
        to_save = []
        for party in parties:
            addr = cls._find_address(party)
            if addr:
                if value is not None:
                    addr.street = value
                    to_save.append(addr)
            elif value:
                Address.create([{
                    'party': party.id,
                    'street': value,
                }])
        if to_save:
            Address.save(to_save)

    @classmethod
    def set_domicilio_ciudad(cls, parties, name, value):
        """Crea o actualiza la ciudad de la primera dirección."""
        pool = Pool()
        Address = pool.get('party.address')
        to_save = []
        for party in parties:
            addr = cls._find_address(party)
            if addr:
                if value is not None:
                    addr.city = value
                    to_save.append(addr)
            elif value:
                Address.create([{
                    'party': party.id,
                    'city': value,
                }])
        if to_save:
            Address.save(to_save)

    @classmethod
    def create(cls, vlist):
        """Exige los datos obligatorios solo al crear la persona.

        Se valida despues de super().create() porque los campos de carga
        rapida (email, telefono, domicilio) son Function con setter y recien
        generan sus registros durante la creacion. Si falta algun dato se
        lanza UserError y Tryton revierte toda la transaccion. Las personas
        ya existentes no se revalidan al editarlas.
        """
        parties = super().create(vlist)
        for party in parties:
            party.check_datos_obligatorios_persona()
        return parties

    def check_datos_obligatorios_persona(self):
        """
        Verifica que si la party es persona (y no institución), tenga:
        - name
        - lastname
        - al menos un contact mechanism de tipo email con valor
        - al menos un contact mechanism de tipo phone o mobile con valor
        - al menos una dirección con calle (street)
        """
        # No se aplica a terceros que no sean personas ni a instituciones
        if not self.is_person or self.is_institution:
            return

        pool = Pool()
        ContactMechanism = pool.get('party.contact_mechanism')
        Address = pool.get('party.address')

        # 1. Nombre obligatorio
        if not self.name or not self.name.strip():
            raise UserError(gettext(
                'persona_datos_obligatorios.msg_persona_name_required'))

        # 2. Apellido obligatorio
        if not self.lastname or not self.lastname.strip():
            raise UserError(gettext(
                'persona_datos_obligatorios.msg_persona_lastname_required'))

        # 3. Contact mechanism tipo email
        cms = self.contact_mechanisms
        if not cms and self.id and self.id > 0:
            cms = ContactMechanism.search([('party', '=', self.id)])

        has_email = any(
            cm.type == 'email' and cm.value and cm.value.strip()
            for cm in (cms or ())
        )
        if not has_email:
            raise UserError(gettext(
                'persona_datos_obligatorios.msg_persona_email_required'))

        # 4. Contact mechanism tipo phone o mobile
        has_phone = any(
            cm.type in ('phone', 'mobile') and cm.value and cm.value.strip()
            for cm in (cms or ())
        )
        if not has_phone:
            raise UserError(gettext(
                'persona_datos_obligatorios.msg_persona_phone_required'))

        # 5. Domicilio con calle
        addrs = self.addresses
        if not addrs and self.id and self.id > 0:
            addrs = Address.search([('party', '=', self.id)])

        has_street = any(
            addr.street and addr.street.strip()
            for addr in (addrs or ())
        )
        if not has_street:
            raise UserError(gettext(
                'persona_datos_obligatorios.msg_persona_address_required'))
