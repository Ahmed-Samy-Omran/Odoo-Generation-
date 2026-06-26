# -*- coding: utf-8 -*-
{
    'name': 'test_module',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Test module for demonstration purposes',
    'author': 'Generated Module',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/test_module_example_views.xml',
        'views/test_module_example_line_views.xml',
        'views/actions.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}