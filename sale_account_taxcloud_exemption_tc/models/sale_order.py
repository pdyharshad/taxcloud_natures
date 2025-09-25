# copyright 2024 Sodexis
# license OPL-1 (see license file for full copyright and licensing details).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_dont_apply_exemption = fields.Boolean(
        string="Don't Apply Exemption",
        copy=False,
        help="Indicates not to apply the exemption to this transaction",
    )
    is_taxcloud = fields.Boolean(related="fiscal_position_id.is_taxcloud")
    taxcloud_exemption_id = fields.Many2one(
        "taxcloud.exemption",
        string="Exemption",
        tracking=3,
        copy=False,
        help="Exemption Certificate Applied",
    )
    is_exemption_not_applied = fields.Boolean(
        string="Exemption is not Applied",
        copy=False,
        help="Indicates exemption not applied to this transaction",
    )

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        res.update(
            {
                "is_dont_apply_exemption": self.is_dont_apply_exemption,
                "taxcloud_exemption_id": self.taxcloud_exemption_id.id,
            }
        )
        return res

    def prepare_taxcloud_request(self):
        request = super().prepare_taxcloud_request()
        if (
            not self.is_dont_apply_exemption
            and self.partner_shipping_id
            and self.is_taxcloud
        ):
            valid_certificate_id = self.env[
                "taxcloud.exemption"
            ].get_validate_certificate(self, self.partner_shipping_id)
            lines = self.order_line.filtered(lambda x: x.display_type not in ("line_note", "line_section"))
            if (lines and sum(lines.mapped('price_subtotal'))) or not self.env.company.is_skip_zero_orders:
                self.taxcloud_exemption_id = valid_certificate_id
            else:
                self.taxcloud_exemption_id = False
            if self.taxcloud_exemption_id and self.taxcloud_exemption_id.certificate_id:
                request.ExemptionCertificate = request.factory.ExemptionCertificate()
                request.ExemptionCertificate.CertificateID = (
                    valid_certificate_id.certificate_id
                )
        return request

    def validate_taxes_on_sales_order(self):
        res = super().validate_taxes_on_sales_order()
        if self.taxcloud_exemption_id and self.total_tax_amount_tc:
            self.is_exemption_not_applied = True
        else:
            self.is_exemption_not_applied = False
        return res
