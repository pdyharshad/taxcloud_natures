# copyright 2024 Sodexis
# license OPL-1 (see license file for full copyright and licensing details).

from odoo import api, fields, models


class GroupOfStates(models.Model):
    _name = "group.of.states"
    _description = "Group Of States"
    _rec_name = "name"

    @api.model
    def _default_country(self):
        return self.env["res.country"].search([("code", "=", "US")]).id

    name = fields.Char(
        required=True,
    )
    country_id = fields.Many2one("res.country", default=_default_country, readonly=True)
    state_ids = fields.Many2many(
        "res.country.state", domain="[('country_id', '=', country_id)]"
    )
