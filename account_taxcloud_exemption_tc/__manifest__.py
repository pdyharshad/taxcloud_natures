# Copyright 2024 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

{
    "name": "TaxCloud Exemption",
    "summary": """""",
    "version": "1.0.0",
    "category": "Accounting/Accounting",
    "website": "https://taxcloud.com/integrations/odoo/",
    "author": "Sodexis, TaxCloud",
    "license": "OPL-1",
    "installable": True,
    "application": False,
    "depends": [
        "base",
        "account",
        "account_taxcloud_tc",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/res_partner_industry.xml",
        "data/certificate_reason.xml",
        "views/res_partner_views.xml",
        "views/res_partner_industry_views.xml",
        "views/purchaser_exemption_reason_views.xml",
        "views/group_of_states_views.xml",
        "views/taxcloud_exemption_views.xml",
        "views/account_move_views.xml",
        "views/account_menuitem.xml",
    ],
    "pre_init_hook": "pre_init_hook",
    "images": ["images/main_screenshot.jpg"],
}
