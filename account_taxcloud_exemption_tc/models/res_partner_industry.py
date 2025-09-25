# copyright 2024 Sodexis
# license OPL-1 (see license file for full copyright and licensing details).

from odoo import fields, models


class ResPartnerIndustry(models.Model):
    _inherit = "res.partner.industry"

    is_taxcloud = fields.Boolean(
        string="Used By TaxCloud",
        help="Indicates whether this information is utilized by TaxCloud ",
    )
    taxcloud_business_type = fields.Text(
        help="Business Type used in the TaxCloud Exemption Certificate"
    )
    code = fields.Char()
