# Copyright 2024 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

from . import models
from . import wizard

from odoo import _
from odoo.exceptions import UserError


def pre_init_hook(env):
    module_obj = env["ir.module.module"]
    sale_module = module_obj.search(
        [("name", "=", "sale"), ("state", "=", "installed")]
    )
    sale_taxcloud_exemption_module = module_obj.search(
        [("name", "=", "sale_account_taxcloud_exemption_tc")]
    )
    if sale_module and not sale_taxcloud_exemption_module:
        raise UserError(
            _(
                """Odoo sales module is in installed state, \
                    but our corresponding TaxCloud Exemption (Sale) module"""
                """ is not available in your system. \
                    \nPlease download from Odoo Apps Store to proceed with the installation"""
            )
        )
