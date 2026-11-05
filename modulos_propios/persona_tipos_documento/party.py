# SPDX-FileCopyrightText: 2026 Proyecto GNU Health
# SPDX-License-Identifier: GPL-3.0-or-later

from trytond.exceptions import UserError
from trytond.i18n import gettext
from trytond.model import fields
from trytond.pool import Pool, PoolMeta


class Party(metaclass=PoolMeta):
    """
    Extensión de party.party para permitir la carga rápida del tipo y el
    número de documento desde el formulario de la persona, sin necesidad
    de entrar a la pestaña de Identificadores.

    Los campos son Function con un setter vacío (para que sean editables en
    el cliente): el dato real se guarda en el primer registro de
    party.identifier de la persona (por eso create() y write() los
    interceptan antes de llamar al core).
    """
    __name__ = 'party.party'

    # Claves de carga rápida que se extraen de los valores antes de
    # delegar en el core, porque los campos Function no tienen setter.
    CLAVES_DOCUMENTO = ('documento_tipo', 'documento_numero')

    documento_tipo = fields.Function(
        fields.Selection('get_documento_tipos', 'Tipo de documento'),
        'get_documento_tipo', setter='set_documento')
    documento_numero = fields.Function(
        fields.Char('Número de documento'),
        'get_documento_numero', setter='set_documento')

    @classmethod
    def set_documento(cls, parties, name, value):
        """
        Setter vacío a propósito: un campo Function sin setter es de solo
        lectura en el cliente (trytond/model/fields/function.py). El guardado
        real lo hacen create() y write(), que sacan estas claves de los
        valores antes de llamar al core, por lo que este método no recibe datos.
        """
        pass

    @classmethod
    def get_documento_tipos(cls):
        """Tipos de documento disponibles: los mismos que ofrece party.identifier."""
        return Pool().get('party.identifier').get_types()

    def _primer_identificador(self):
        """
        Devuelve el primer party.identifier de la persona (menor sequence y
        luego menor id) o None. Si la persona todavía no está guardada
        (self.id es None o negativo) devuelve None, porque en ese momento el
        identificador no puede existir en la base.
        """
        if not self.id or self.id < 0:
            return None
        pool = Pool()
        Identifier = pool.get('party.identifier')
        identifiers = Identifier.search([
            ('party', '=', self.id),
        ], order=[('sequence', 'ASC'), ('id', 'ASC')], limit=1)
        if identifiers:
            return identifiers[0]
        return None

    def get_documento_tipo(self, name):
        """Tipo del primer identificador de la persona, o None."""
        identifier = self._primer_identificador()
        if identifier:
            return identifier.type
        return None

    def get_documento_numero(self, name):
        """Número (code) del primer identificador de la persona, o None."""
        identifier = self._primer_identificador()
        if identifier:
            return identifier.code
        return None

    @classmethod
    def create(cls, vlist):
        """
        Crea las personas guardando el tipo y el número de documento en
        party.identifier cuando vienen en la carga rápida.

        Se trabaja sobre una copia de cada diccionario para no modificar los
        valores originales del llamador.
        """
        datos_documento = []
        vlist_limpia = []
        for valores in vlist:
            valores = dict(valores)
            datos = {clave: valores.pop(clave)
                for clave in cls.CLAVES_DOCUMENTO if clave in valores}
            datos_documento.append(datos)
            vlist_limpia.append(valores)

        parties = super().create(vlist_limpia)

        for party, datos in zip(parties, datos_documento):
            if datos:
                party._guardar_documento(datos)
        return parties

    @classmethod
    def write(cls, *args):
        """
        Actualiza las personas guardando el tipo y el número de documento en
        party.identifier cuando vienen en la carga rápida.
        """
        actions = iter(args)
        nuevos_args = []
        pendientes = []
        for parties, valores in zip(actions, actions):
            valores = dict(valores)
            datos = {clave: valores.pop(clave)
                for clave in cls.CLAVES_DOCUMENTO if clave in valores}
            nuevos_args.append(parties)
            nuevos_args.append(valores)
            pendientes.append((parties, datos))

        super().write(*nuevos_args)

        for parties, datos in pendientes:
            if not datos:
                continue
            for party in parties:
                party._guardar_documento(datos)

    def _guardar_documento(self, datos):
        """
        Guarda el tipo y/o el número de documento recibidos en la carga rápida
        sobre el primer identificador de la persona. Si la persona todavía no
        tiene identificador se crea uno, y en ese caso se exige que vengan
        ambos datos.

        La validación del código no se reimplementa: la realiza
        party.identifier (check_code) al crear o escribir el identificador.
        """
        tipo = datos.get('documento_tipo')
        numero = datos.get('documento_numero')
        if isinstance(numero, str):
            numero = numero.strip()
        if tipo == '':
            tipo = None

        # Si no llegó ninguno de los dos datos (o llegaron vacíos) no se hace nada.
        if not tipo and not numero:
            return

        pool = Pool()
        Identifier = pool.get('party.identifier')

        existente = self._primer_identificador()

        # 1) Ya hay un identificador: se actualizan solo los datos recibidos.
        if existente:
            cambios = {}
            if tipo:
                cambios['type'] = tipo
            if numero:
                cambios['code'] = numero
            if cambios:
                Identifier.write([existente], cambios)
            return

        # 2) No hay identificador: al crear uno se exigen tipo y número juntos.
        if not tipo or not numero:
            raise UserError(gettext(
                'persona_tipos_documento.msg_documento_incompleto'))

        Identifier.create([{
            'party': self.id,
            'type': tipo,
            'code': numero,
        }])
