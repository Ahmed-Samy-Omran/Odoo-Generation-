# -*- coding: utf-8 -*-
{
    'name': 'my_test_module',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Test module for demonstration purposes',
    'author': 'Generated Module',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/my_test_module_test_model_views.xml',
        'views/actions.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}