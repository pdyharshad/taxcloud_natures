# copyright 2024 Sodexis
# license OPL-1 (see license file for full copyright and licensing details).

from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    first_name = fields.Char(
        string="TaxCloud First Name",
        help="First Name used in the TaxCloud. "
        "If filled, the Name field will be computed"
        " using the First Name and Last Name.",
    )
    last_name = fields.Char(
        string="TaxCloud Last Name",
        help="Last Name used in the TaxCloud. If filled, "
        "the Name field will be computed using the First Name and Last Name.",
    )
    tax_number_type = fields.Selection(
        selection=[
            ("StateIssued", "Driver's License/State Issued ID"),
            ("FEIN", "Federal Employer Identification"),
            ("ForeignDiplomat", "Foreign Diplomat"),
            ("SSN", "Social Security"),
            ("TaxID", "Tax ID"),
        ],
        default="TaxID",
        required=True,
        help="The type of tax number will be used in the TaxCloud exemption.",
    )
    state_of_issue_id = fields.Many2one(
        "res.country.state",
        store=True,
        domain=lambda self: [("country_id", "=", self.env.ref("base.us").id)],
        help="State where the tax number or exemption certificate was issued.",
    )
    other_business_type = fields.Char(
        help="Specifies the type of business "
        "if it does not fall under the predefined Business Type."
    )
    is_other_services = fields.Boolean(compute="_compute_is_other_services")

    def _compute_is_other_services(self):
        other_services_id = self.env.ref("base.res_partner_industry_S").id
        for record in self:
            record.is_other_services = record.industry_id.id == other_services_id

    @api.onchange("industry_id")
    def _onchange_industry_id(self):
        self._compute_is_other_services()

    @api.onchange("state_id")
    def _onchange_state_id(self):
        if not self.state_of_issue_id and self.state_id:
            self.state_of_issue_id = self.state_id

    def write(self, vals):
        res = super().write(vals)
        if ("first_name" in vals) or ("last_name" in vals):
            if self.first_name and self.last_name:
                self.name = self.first_name + " " + self.last_name
            elif self.first_name or self.last_name:
                self.name = self.first_name or self.last_name
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            first_name = vals.get("first_name", False)
            last_name = vals.get("last_name", False)
            if first_name and last_name:
                vals["name"] = first_name + " " + last_name
            elif first_name or last_name:
                vals["name"] = first_name or last_name
        return super().create(vals_list)

    def action_open_exemption_certificate(self):
        if self.parent_id and self.child_ids:
            related_taxcloud_exemption_ids = self.env[
                "taxcloud.exemption"
            ].get_all_certificates(self) | self.env[
                "taxcloud.exemption"
            ].get_all_child_certificates(
                self
            )
        elif self.parent_id:
            related_taxcloud_exemption_ids = self.env[
                "taxcloud.exemption"
            ].get_all_certificates(self)
        else:
            related_taxcloud_exemption_ids = self.env[
                "taxcloud.exemption"
            ].get_all_child_certificates(self)
        result = {
            "type": "ir.actions.act_window",
            "name": _("Exemption Certificate"),
            "res_model": "taxcloud.exemption",
            "domain": [["id", "in", related_taxcloud_exemption_ids.ids]],
            "view_mode": "list,form",
            "context": {"search_default_active": True},
        }
        if len(related_taxcloud_exemption_ids) == 1:
            result["view_mode"] = "form"
            result["res_id"] = related_taxcloud_exemption_ids.id
        return result
