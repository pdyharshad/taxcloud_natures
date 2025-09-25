from odoo import models


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    def _prepare_default_reversal(self, move):
        res = super()._prepare_default_reversal(move)
        if move.taxcloud_exemption_id:
            res.update({"taxcloud_exemption_id": move.taxcloud_exemption_id.id})
        if move.is_dont_apply_exemption:
            res.update({"is_dont_apply_exemption": True})
        return res
