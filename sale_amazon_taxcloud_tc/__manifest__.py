{
    "name": "Amazon/TaxCloud Bridge",
    "summary": """This is the official Odoo Tax Cloud integration supported by Taxcloud.
    Bridge module between Amazon Connector and TaxCloud""",
    "category": "Sales/Sales",
    "version": "1.0.0",
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "depends": ["sale_amazon", "account_taxcloud_tc"],
    "auto_install": True,
    "license": "LGPL-3",
    "author": "Odoo S.A., Sodexis, TaxCloud",
    "website": "https://taxcloud.com/integrations/odoo/",
    "live_test_url": "https://sodexis.com/odoo-apps-store-demo",
    "images": ["images/main_screenshot.jpg"],
}
