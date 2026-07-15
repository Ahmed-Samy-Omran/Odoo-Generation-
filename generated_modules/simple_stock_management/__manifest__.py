# -*- coding: utf-8 -*-
{
    'name': 'simple_stock_management',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'A simple stock management system with products and stock moves tracking.',
    'author': 'Generated Module',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/product_product_views.xml',
        'views/stock_move_views.xml',
        'views/actions.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}