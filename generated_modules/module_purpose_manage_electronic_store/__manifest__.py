# -*- coding: utf-8 -*-
{
    'name': 'module_purpose_manage_electronic_store',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Manage electronic store operations including product inventory and sales tracking.',
    'author': 'Generated Module',
    'depends': ['base', 'sale', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/product_product_views.xml',
        'views/product_category_views.xml',
        'views/sale_order_views.xml',
        'views/sale_order_line_views.xml',
        'views/res_partner_views.xml',
        'views/actions.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}