# -*- coding: utf-8 -*-
{
    'name': 'gym_shop',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Manages sales of products and inventory within the gym.',
    'author': 'Generated Module',
    'depends': ['base', 'gym_core'],
    'data': [
        'security/ir.model.access.csv',
        'views/gym_shop_product_views.xml',
        'views/gym_shop_sale_order_views.xml',
        'views/gym_shop_sale_order_line_views.xml',
        'views/actions.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}