from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    reward_id = fields.Many2one(
        "loyalty.reward",
        string="Discount reward",
        readonly=True,
        help="The loyalty reward that created this line.",
    )
    # Technical field to hold prices for TaxCloud
    price_taxcloud = fields.Float("Taxcloud Price", default=0)
    is_reward_line = fields.Boolean(string="Is a program reward line")

    def _get_taxcloud_price(self):
        self.ensure_one()
        return self.price_taxcloud
