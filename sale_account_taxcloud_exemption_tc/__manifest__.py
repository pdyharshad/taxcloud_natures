# Copyright 2024 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

{
    "name": "TaxCloud Exemption (Sale)",
    "summary": """""",
    "version": "1.0.0",
    "category": "Accounting/Accounting",
    "website": "https://taxcloud.com/integrations/odoo/",
    "author": "Sodexis, TaxCloud",
    "license": "OPL-1",
    "installable": True,
    "application": False,
    "auto_install": True,
    "depends": [
        "sale_account_taxcloud_tc",
        "account_taxcloud_exemption_tc",
    ],
    "data": [
        "views/sale_order_views.xml",
    ],
    "images": ["images/main_screenshot.jpg"],
}
