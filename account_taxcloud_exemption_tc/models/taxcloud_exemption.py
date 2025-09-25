# See LICENSE file for full copyright and licensing details.

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .taxcloud_request import TaxCloudRequest


class TaxcloudExemption(models.Model):
    _name = "taxcloud.exemption"
    _description = "Taxcloud Exemption"

    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True

    def _company_ids_domain(self):
        return [
            (
                "id",
                "in",
                self.env.company.ids + self.env.context.get("allowed_company_ids", []),
            )
        ]

    # HEADER FIELDS
    name = fields.Char(compute="_compute_display_name", store=True)
    display_name = fields.Char(compute="_compute_display_name", store=True)
    certificate_id = fields.Char(string="Certificate ID", copy=False)
    partner_id = fields.Many2one("res.partner", string="Customer", check_company=True)
    tax_number_type = fields.Selection(
        selection=[
            ("StateIssued", "Driver's License/State Issued ID"),
            ("FEIN", "Federal Employer Identification"),
            ("ForeignDiplomat", "Foreign Diplomat"),
            ("SSN", "Social Security"),
            ("TaxID", "Tax ID"),
        ],
        help="The type of tax number will be used in the TaxCloud exemption.",
    )
    vat = fields.Char(
        string="Tax ID",
    )
    state_of_issue_id = fields.Many2one(
        "res.country.state",
        store=True,
        domain=lambda self: [("country_id", "=", self.env.ref("base.us").id)],
        help="State where the tax number or exemption certificate was issued.",
    )
    industry_id = fields.Many2one(
        "res.partner.industry",
        string="Business Type",
        help="Specifies the type of entity",
    )
    is_other_services = fields.Boolean()
    other_business_type = fields.Char(
        help="Specifies the type of business "
        "if it does not fall under the predefined Business Type."
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("export", "Exported"),
            ("cancel", "Cancelled"),
        ],
        string="Stage",
        readonly=True,
        copy=False,
        index=True,
        tracking=True,
        default="draft",
    )

    # EXEMPTION CERTIFICATE INFORMATION FIELDS
    start_date = fields.Date(default=fields.Date.context_today)
    expiration_date = fields.Date()
    creation_date = fields.Date(default=fields.Date.today)
    certificate_reason = fields.Many2one(
        "purchaser.exemption.reason",
        help="Reason for issuing the exemption certificate",
    )
    is_other_reason = fields.Boolean()
    other_reason = fields.Char(
        help="Specifies the purpose for issuing the exemption"
        " certificate if it does not fall under the predefined Certificate Reason."
    )
    is_expired = fields.Boolean(compute="_compute_is_expired")

    # EXEMPTION STATE AND IT'S DETAILS FIELDS
    group_of_state_id = fields.Many2one("group.of.states", string="Group of States")
    state_ids = fields.Many2many(
        "res.country.state",
        string="States",
        domain=lambda self: [("country_id", "=", self.env.ref("base.us").id)],
    )
    reason_for_exemption = fields.Char()
    id_number = fields.Char(string="ID Number")

    taxcloud_exemption_line_ids = fields.One2many(
        "taxcloud.exemption.line",
        "taxcloud_exemption_id",
        string="Taxcloud Exemption Line",
        copy=True,
    )
    company_id = fields.Many2one(
        "res.company", "Company", index=True, domain=_company_ids_domain
    )
    sale_order_count = fields.Integer(
        compute="_compute_sale_order_count", string="Sale Order Count"
    )
    invoice_count = fields.Integer(
        compute="_compute_invoice_count", string="Invoice Count"
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.company:
            res.update({"company_id": self.env.company.id})
        return res

    @api.depends("partner_id", "state_ids")
    def _compute_display_name(self):
        for exemption in self:
            state_codes = ", ".join(exemption.state_ids.mapped("code"))
            customer_name = exemption.partner_id.name or ""
            name = f"{customer_name}"
            if state_codes:
                name += f" ({state_codes})"
            exemption.name = name
            exemption.display_name = name

    def _compute_is_expired(self):
        for rec in self:
            rec.is_expired = bool(
                rec.expiration_date and (fields.Date.today() > rec.expiration_date)
            )

    def _compute_sale_order_count(self):
        for rec in self:
            sale_order_ids = self.env["sale.order"].search(
                [("taxcloud_exemption_id", "=", rec.id)]
            )
            rec.sale_order_count = len(sale_order_ids)

    def _compute_invoice_count(self):
        for rec in self:
            invoice_ids = self.env["account.move"].search(
                [("taxcloud_exemption_id", "=", rec.id)]
            )
            rec.invoice_count = len(invoice_ids)

    @api.onchange("state_ids")
    def _onchange_state_ids(self):
        self._update_taxcloud_exemption_lines(
            self.state_ids.ids,
            list(
                set(self.taxcloud_exemption_line_ids.mapped("state_id").ids)
                - set(self.state_ids.ids)
            ),
        )

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        industry_id = self.partner_id.industry_id
        self.industry_id = (
            industry_id if industry_id and industry_id.is_taxcloud else None
        )
        self.tax_number_type = self.partner_id.tax_number_type
        self.vat = self.partner_id.vat
        self.state_of_issue_id = self.partner_id.state_of_issue_id

    @api.onchange("industry_id")
    def _onchange_industry_id(self):
        industry_id = self.industry_id
        if (
            industry_id
            and industry_id.get_external_id().get(industry_id.id)
            == "base.res_partner_industry_S"
        ):
            self.is_other_services = True
            self.other_business_type = self.partner_id.other_business_type
        else:
            self.is_other_services = False

    @api.onchange("group_of_state_id")
    def _onchange_group_of_state_id(self):
        if self.group_of_state_id:
            state_ids = self.group_of_state_id.state_ids
            self.state_ids = [Command.set(state_ids.ids)]
        else:
            self.state_ids = [Command.clear()]

    @api.onchange("certificate_reason")
    def _onchange_certificate_reason(self):
        self.is_other_reason = bool(
            self.certificate_reason and self.certificate_reason.other_reason
        )

    def action_export_exemption(self):
        try:
            self.action_add_exemption_certificate()
            self.message_post(body=_("Export Exemption Successful"))
            self.write({"state": "export"})
        except Exception as e:
            self.message_post(body=_("Export Exemption Failed: %s" % str(e)))

    def action_cancel(self):
        try:
            self.action_delete_exemption_certificate()
            self.message_post(body=_("Export Exemption Cancelled"))
            self.write({"state": "cancel"})
        except Exception as e:
            self.message_post(body=_("Couldn't Cancel Export Exemption: %s" % str(e)))

    @api.model
    def _get_TaxCloudRequest(self, api_id, api_key):
        return TaxCloudRequest(api_id, api_key)

    def action_add_exemption_certificate(self):
        company = self.partner_id.company_id
        shipper = company or self.env.company
        api_id = shipper.taxcloud_api_id
        api_key = shipper.taxcloud_api_key
        request = self._get_TaxCloudRequest(api_id, api_key)
        request.set_exemption_certificate_details(self)
        response = request.add_exemption_certificate()
        if response.get("error_message"):
            raise ValidationError(
                _("Unable to Add Exception Certificate in TaxCloud: ")
                + "\n"
                + response["error_message"]
            )
        values = response["values"]
        self.write({"certificate_id": values["certificate_id"]})

    def action_delete_exemption_certificate(self):
        company = self.partner_id.company_id
        shipper = company or self.env.company
        api_id = shipper.taxcloud_api_id
        api_key = shipper.taxcloud_api_key
        request = self._get_TaxCloudRequest(api_id, api_key)
        response = request.delete_exemption_certificate(self.certificate_id)
        if response.get("error_message"):
            raise ValidationError(
                _("Unable to Delete Exception Certificate in TaxCloud: ")
                + "\n"
                + response["error_message"]
            )
        values = response["values"]
        self.write({"certificate_id": values["certificate_id"]})

    def _update_taxcloud_exemption_lines(self, state_ids_to_add, state_ids_to_remove):
        existing_state_ids = self.taxcloud_exemption_line_ids.mapped("state_id.id")

        # Add new lines for state_ids_to_add that are not already present
        new_state_ids_to_add = list(set(state_ids_to_add) - set(existing_state_ids))
        if new_state_ids_to_add:
            taxcloud_exemption_line_ids_commands = [
                Command.create(
                    {
                        "taxcloud_exemption_id": self.id,
                        "state_id": state.id,
                        "state_code": state.code,
                        "reason_for_exemption": self.reason_for_exemption,
                        "id_number": self.id_number,
                    }
                )
                for state in self.env["res.country.state"].browse(new_state_ids_to_add)
            ]
            self.taxcloud_exemption_line_ids = taxcloud_exemption_line_ids_commands

        if state_ids_to_remove:
            self.taxcloud_exemption_line_ids = [
                Command.unlink(line.id)
                for line in self.taxcloud_exemption_line_ids
                if line.state_id.id in state_ids_to_remove
            ]

    def get_first_and_last_name(self):
        first_name = self.partner_id.first_name or ""
        last_name = self.partner_id.last_name or ""
        if not first_name and not last_name:
            name = self.partner_id.name.split(" ", 1)
            if len(name) > 1:
                first_name = name[0]
                last_name = name[1]
            else:
                first_name = self.partner_id.name
        return dict({"first_name": first_name, "last_name": last_name})

    def get_validate_certificate(self, record, partner):
        rec_date = None
        certificate_id = None
        rec_date = self.get_record_date(record)
        domain = [
            ("state", "=", "export"),
            ("start_date", "<=", rec_date),
            ("company_id", "=", record.company_id.id),
            ("state_ids", "in", partner.state_id.ids),
            "|",
            ("expiration_date", ">=", rec_date),
            ("expiration_date", "=", False),
        ]
        if partner:
            certificate_id = self.search(
                domain + [("partner_id", "=", partner.id)], limit=1
            )
            if not certificate_id:
                certificate_id = self.search(
                    domain + [("partner_id", "=", partner.commercial_partner_id.id)],
                    limit=1,
                )
        return certificate_id

    def get_record_date(self, record):
        today = (
            fields.Datetime.today()
            if record._name == "sale.order"
            else fields.Date.today()
        )
        if record._name == "sale.order":
            rec_date = (
                record.date_order
                if record.date_order and record.date_order >= today
                else today
            )
        elif record._name == "account.move":
            rec_date = (
                record.invoice_date
                if record.invoice_date and record.invoice_date >= today
                else today
            )
        return rec_date

    def get_all_certificates(self, partner):
        exemption_certificates = self.env["taxcloud.exemption"].search(
            [
                (
                    "partner_id",
                    "in",
                    ([partner.id] + partner.commercial_partner_id.ids),
                ),
            ]
        )
        return exemption_certificates

    def get_all_child_certificates(self, partner):
        exemption_certificates = self.env["taxcloud.exemption"].search(
            [
                ("partner_id", "child_of", partner.id),
            ]
        )
        return exemption_certificates

    def action_view_sale_order(self):
        sale_order_ids = self.env["sale.order"].search(
            [("taxcloud_exemption_id", "=", self.id)]
        )
        result = {
            "type": "ir.actions.act_window",
            "name": _("Sales"),
            "res_model": "sale.order",
            "domain": [["id", "in", sale_order_ids.ids]],
            "view_mode": "list,form",
        }
        if len(sale_order_ids) == 1:
            result["view_mode"] = "form"
            result["res_id"] = sale_order_ids.id
        return result

    def action_view_invoice(self):
        invoice_ids = self.env["account.move"].search(
            [("taxcloud_exemption_id", "=", self.id)]
        )
        result = {
            "type": "ir.actions.act_window",
            "name": _("Invoices"),
            "res_model": "account.move",
            "domain": [["id", "in", invoice_ids.ids]],
            "view_mode": "list,form",
        }
        if len(invoice_ids) == 1:
            result["view_mode"] = "form"
            result["res_id"] = invoice_ids.id
        return result

    def export_exemption(self):
        records = self.filtered(lambda x:x.state != 'draft')
        if records:
            raise UserError(_('There is no exemption in the stage to get the certificate ID'))
        for exemption in self:
            exemption.action_export_exemption()


class TaxcloudExemptionLine(models.Model):
    _name = "taxcloud.exemption.line"
    _description = "Taxcloud Exemption Line"

    sequence = fields.Integer(default=10)
    taxcloud_exemption_id = fields.Many2one(
        "taxcloud.exemption", ondelete="cascade", readonly=True
    )
    state_id = fields.Many2one(
        "res.country.state",
        string="States",
        required=True,
        domain=lambda self: [("country_id", "=", self.env.ref("base.us").id)],
    )
    state_code = fields.Char(related="state_id.code")
    reason_for_exemption = fields.Char()
    id_number = fields.Char(string="ID Number")

    def unlink(self):
        exemption_ids = self.mapped("taxcloud_exemption_id")
        states_ids_to_remove = self.mapped("state_id")
        res = super().unlink()
        for exemption in exemption_ids:
            exemption.state_ids = [
                Command.unlink(state.id) for state in states_ids_to_remove
            ]
        return res
