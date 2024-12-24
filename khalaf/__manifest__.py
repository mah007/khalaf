{
    'name': 'Khalaf Sons Grocery Delivery Management',
    'version': '1.0',
    'summary': 'Efficient Delivery Management for Khalaf Sons Grocery Shop',
    'description': """
Khalaf Sons Grocery Delivery Management Module

This module is specifically designed for Khalaf Sons, a grocery shop similar to Awlad Ragab. The module aims to streamline delivery operations by assigning delivery pickups to employees (delivery boys) and tracking their progress. Key features include:

- Assign delivery orders to delivery boys (employees).
- Monitor delivery statuses in real-time.
- Automate the completion of delivery boy trips when all assigned orders are done.
- Provide a wizard to assign delivery boys to multiple orders from a tree view.
- Dashboard view displaying:
    - Delivery boys and the number of assigned orders.
    - Total amount to be collected (cash and visa breakdown).
    - Performance metrics for delivery efficiency.

This module enhances the operational efficiency of grocery delivery services, ensuring timely and accurate deliveries while maintaining customer satisfaction.

""",
    'author': 'Mahmoud',
    'website': 'http://www.mah007.net',
    'category': 'Operations/Inventory',
    'depends': ['stock', 'hr', 'sale','pos_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_receipt_report.xml',
        'views/delivery_boy_views.xml',
        'views/res_partner.xml',
        'views/sale_order.xml',
        'views/hr_employee.xml',
        'views/assign_delivery_boy_wizard_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'khalaf/static/src/js/sale_order_fetcher.js',
            'khalaf/static/src/xml/sale_order_list.xml',
            'khalaf/static/src/xml/sale_order_row_ext.xml'
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
