from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class ComchainPartnersInfo(Datamodel):
    _name = "cyclos.partners.info"

    addresses = fields.List(fields.String(), required=True)


class CyclosCreditInfo(Datamodel):
    _name = "cyclos.credit.info"

    owner_id = fields.Integer(required=True)
    amount = fields.Float(required=True)


class CyclosCreditResponse(Datamodel):
    _name = "cyclos.credit.response"

    order_url = fields.String(required=True)
