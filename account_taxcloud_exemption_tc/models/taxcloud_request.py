import logging

from zeep.exceptions import Fault

from odoo import _

from odoo.addons.account_taxcloud_tc.models import taxcloud_request

_logger = logging.getLogger(__name__)


class TaxCloudRequest(taxcloud_request.TaxCloudRequest):
    def set_exemption_certificate_details(self, exemption_certificate):
        self.customer_id = exemption_certificate.partner_id.id
        self.exemption_certificate = self.factory.ExemptionCertificate()
        self.exemption_certificate.Detail = self.factory.ExemptionCertificateDetail()
        self.exemption_certificate.Detail.ExemptStates = (
            self.factory.ArrayOfExemptState()
        )
        self.exemption_certificate.Detail.ExemptStates.ExemptState = (
            self._process_exempt_states(
                exemption_certificate.taxcloud_exemption_line_ids
            )
        )
        self.exemption_certificate.Detail.PurchaserTaxID = self.factory.TaxID()
        self.exemption_certificate.Detail.PurchaserTaxID.TaxType = (
            exemption_certificate.tax_number_type
        )
        self.exemption_certificate.Detail.PurchaserTaxID.IDNumber = (
            exemption_certificate.vat or ""
        )
        self.exemption_certificate.Detail.PurchaserTaxID.StateOfIssue = (
            exemption_certificate.state_of_issue_id.code
        )
        if (
            exemption_certificate.partner_id.company_type != "company"
            and exemption_certificate.partner_id.title
        ):
            self.exemption_certificate.Detail.PurchaserTitle = (
                exemption_certificate.partner_id.title.name
            )
        self.exemption_certificate.Detail.SinglePurchase = (
            False  # exemption_certificate.is_single_purchase
        )
        self.exemption_certificate.Detail.PurchaserFirstName = (
            exemption_certificate.get_first_and_last_name().get("first_name", "")
        )
        self.exemption_certificate.Detail.PurchaserLastName = (
            exemption_certificate.get_first_and_last_name().get("last_name", "")
        )
        self.exemption_certificate.Detail.PurchaserAddress1 = (
            exemption_certificate.partner_id.street or ""
        )
        self.exemption_certificate.Detail.PurchaserAddress2 = (
            exemption_certificate.partner_id.street2 or ""
        )
        self.exemption_certificate.Detail.PurchaserCity = (
            exemption_certificate.partner_id.city
        )
        self.exemption_certificate.Detail.PurchaserState = (
            exemption_certificate.partner_id.state_id.code
        )
        self.exemption_certificate.Detail.PurchaserZip = (
            exemption_certificate.partner_id.zip
        )
        self.exemption_certificate.Detail.PurchaserBusinessType = (
            exemption_certificate.industry_id.code
        )
        self.exemption_certificate.Detail.PurchaserExemptionReason = (
            exemption_certificate.certificate_reason.code
        )
        self.exemption_certificate.Detail.CreatedDate = (
            exemption_certificate.creation_date
        )

    def _process_exempt_states(self, exemption_state_ids):
        exemption_state_items = []
        for exemption_state_id in exemption_state_ids:
            exempt_state = self.factory.ExemptState()
            exempt_state.StateAbbr = exemption_state_id.state_code
            exempt_state.ReasonForExemption = exemption_state_id.reason_for_exemption
            exempt_state.IdentificationNumber = exemption_state_id.id_number
            exemption_state_items.append(exempt_state)
        return exemption_state_items

    def add_exemption_certificate(self):
        customer_id = self.customer_id or "NoCustomerID"
        formatted_response = {}
        if not self.api_login_id or not self.api_key:
            formatted_response["error_message"] = _(
                "Please configure taxcloud credentials on the current company "
                "or use a different fiscal position"
            )
            return formatted_response
        try:
            response = self.client.service.AddExemptCertificate(
                self.api_login_id, self.api_key, customer_id, self.exemption_certificate
            )
            formatted_response["response"] = response
            if response.ResponseType == "OK":
                formatted_response["values"] = {
                    "certificate_id": response.CertificateID,
                    "messages": response.Messages,
                }
            elif response.ResponseType == "Error":
                formatted_response["error_message"] = response.Messages.ResponseMessage[
                    0
                ].Message
        except Fault as fault:
            formatted_response["error_message"] = fault.message
        except OSError:
            formatted_response["error_message"] = "TaxCloud Server Not Found"
        return formatted_response

    def delete_exemption_certificate(self, certificate_id):
        formatted_response = {}
        if not certificate_id:
            formatted_response["error_message"] = _(
                "Can't cancel Exemption without certificate ID"
            )
            return formatted_response
        if not self.api_login_id or not self.api_key:
            formatted_response["error_message"] = _(
                "Please configure taxcloud credentials on the current company "
                "or use a different fiscal position"
            )
            return formatted_response
        try:
            response = self.client.service.DeleteExemptCertificate(
                self.api_login_id,
                self.api_key,
                certificate_id,
            )
            formatted_response["response"] = response
            if response.ResponseType == "OK":
                formatted_response["values"] = {
                    "certificate_id": None,
                    "messages": response.Messages,
                }
            elif response.ResponseType == "Error":
                formatted_response["error_message"] = response.Messages.ResponseMessage[
                    0
                ].Message
        except Fault as fault:
            formatted_response["error_message"] = fault.message
        except OSError:
            formatted_response["error_message"] = "TaxCloud Server Not Found"
        return formatted_response
