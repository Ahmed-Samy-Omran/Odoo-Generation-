# -*- coding: utf-8 -*-
{
    'name': 'health_management',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Health Record Management System',
    'author': 'Generated Module',
    'depends': ['base', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/health_management_health_record_views.xml',
        'views/actions.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}