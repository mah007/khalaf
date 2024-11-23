# -*- coding: utf-8 -*-
{
    'name': "Bosta Shipping",
    'description': "Send your shippings through Bosta and track them online",

    'author': "Ramadan Khalil,2segypt",
    'website': "https://www.linkedin.com/in/ramadan-khalil-a7088164/",
    'category': 'Operations/Inventory/Delivery',
    'version': '17.1',
    'price': 150,
    'currency': 'USD',
    'depends': ['stock_delivery'],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/delivery_bosta_view.xml',
        'views/stock_picking_view.xml',
        # 'views/res_config_settings_views.xml',
        'wizard/bosta_wizard_view.xml',
        'data/ir_cron.xml',
        'data/data.xml'
    ],
    'license': 'OPL-1',
}
