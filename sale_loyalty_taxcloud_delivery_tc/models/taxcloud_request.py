from odoo.addons.sale_loyalty_taxcloud_tc.models import taxcloud_request


class TaxCloudRequest(taxcloud_request.TaxCloudRequest):
    """We want the delivery reward to be computed independently.
    With sale_coupon_delivery, delivery line are not discountable anymore.
    (Note that coupon and delivery can be installed without sale_coupon_delivery.)
    """

    def _rank_discount_line(self, line):
        res = super()._rank_discount_line(line)
        res.insert(0, line.reward_id.reward_type != "shipping")
        return res

    def _get_discountable_lines(self, discount_line, lines):
        lines = super()._get_discountable_lines(discount_line, lines)
        if discount_line.reward_id.reward_type == "shipping":
            lines = lines.filtered(lambda x: x._is_delivery())
        else:
            lines = lines.filtered(lambda x: not x._is_delivery())
        return lines
