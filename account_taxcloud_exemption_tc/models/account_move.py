# copyright 2024 Sodexis
# license OPL-1 (see license file for full copyright and licensing details).
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

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
        help="Exemption Certificate applied",
    )
    is_exemption_not_applied = fields.Boolean(
        string="Exemption is not Applied",
        copy=False,
        help="Indicates exemption not applied to this transaction",
    )

    def prepare_taxcloud_request(self):
        request = super().prepare_taxcloud_request()
        if (
            not self.is_dont_apply_exemption
            and self.partner_shipping_id
            and self.is_taxcloud
        ):
            if (
                self.move_type == "out_refund"
                and self.reversed_entry_id
                and self.reversed_entry_id.move_type == "out_invoice"
                and not self.reversed_entry_id.taxcloud_exemption_id
            ):
                return request
            valid_certificate_id = self.env[
                "taxcloud.exemption"
            ].get_validate_certificate(self, self.partner_shipping_id)
            if self.move_type == 'out_refund':
                taxcloud_exemption_ids = self.mapped('invoice_line_ids.sale_line_ids.invoice_lines.move_id').filtered(
                lambda x: x.move_type == 'out_invoice').mapped('taxcloud_exemption_id') or self.reversed_entry_id.taxcloud_exemption_id
                if not valid_certificate_id and taxcloud_exemption_ids:
                    valid_certificate_id = taxcloud_exemption_ids[0]
            lines = self.invoice_line_ids.filtered(lambda x: x.display_type not in ("line_note", "line_section"))
            if (lines and sum(lines.mapped('price_subtotal'))) or not self.env.company.is_skip_zero_invoice:
                self.taxcloud_exemption_id = valid_certificate_id
            else:
                self.taxcloud_exemption_id = False
            if self.taxcloud_exemption_id and self.taxcloud_exemption_id.certificate_id:
                request.ExemptionCertificate = request.factory.ExemptionCertificate()
                request.ExemptionCertificate.CertificateID = (
                    valid_certificate_id.certificate_id
                )
        return request

    def validate_taxes_on_invoice(self):
        res = super().validate_taxes_on_invoice()
        if self.taxcloud_exemption_id and self.total_tax_amount_tc:
            self.is_exemption_not_applied = True
        else:
            self.is_exemption_not_applied = False
        return res
