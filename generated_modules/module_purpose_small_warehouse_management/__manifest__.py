# -*- coding: utf-8 -*-
{
    'name': 'module_purpose_small_warehouse_management',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Small warehouse management system with products and invoices.',
    'author': 'Generated Module',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/product_views.xml',
        'views/invoice_views.xml',
        'views/invoice_line_views.xml',
        'views/actions.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}