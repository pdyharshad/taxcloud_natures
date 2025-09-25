from odoo import models


class SaleOrderOption(models.Model):
    _inherit = "sale.order.option"

    def add_option_to_order(self):
        res = super().add_option_to_order()
        sale_order = self.order_id
        if sale_order:
            sale_order.add_option_to_order_with_taxcloud()
        return res
