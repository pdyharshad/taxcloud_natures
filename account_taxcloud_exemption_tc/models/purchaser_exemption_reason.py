# copyright 2024 Sodexis
# license OPL-1 (see license file for full copyright and licensing details).

from odoo import fields, models


class PurchaserExemptionReason(models.Model):
    _name = "purchaser.exemption.reason"
    _description = "Purchaser Exemption Reason"
    _rec_name = "name"

    name = fields.Char(
        required=True,
    )
    other_reason = fields.Boolean()
    code = fields.Char()
