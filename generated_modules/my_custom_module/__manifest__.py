# -*- coding: utf-8 -*-
{
    'name': 'my_custom_module',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'My Custom Module for Odoo 17.0',
    'author': 'Generated Module',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/my_custom_module_my_model_views.xml',
        'views/actions.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}