# -*- coding: utf-8 -*-

try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None
from io import BytesIO

from odoo import models, fields, api
from odoo.exceptions import UserError


class Partners(models.Model):
    _inherit = "res.partner"

    qr = fields.Binary(string="Member QR code")
    qr_content = fields.Char(string="QR code content")
    qr_url = fields.Char(string="Member QR code URL")

    @api.multi
    def generate_qr(self):
        if qrcode and base64:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            self.qr_content = (
                self.env["ir.config_parameter"].sudo().get_param("web.base.url")
                + self.website_url
            )
            qr.add_data(self.qr_content)
            qr.make(fit=True)

            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
            self.write({"qr": qr_image})
            self.qr_url = (
                self.env["ir.config_parameter"].sudo().get_param("web.base.url")
                + "/web/content/res.partner/"
                + str(self.id)
                + "/qr"
            )
            return self.env.ref("lcc_members_qr.print_qr").report_action(
                self, data={"data": self.id, "type": "cust"}
            )
        else:
            raise UserError(
                _(
                    "Necessary requirements are not satisfied - Need qrcode and base64 Python libraries"
                )
            )
