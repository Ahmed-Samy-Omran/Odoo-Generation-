# -*- coding: utf-8 -*-
{
    'name': 'school_management',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Complete school management system',
    'author': 'Generated Module',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/student_views.xml',
        'views/teacher_views.xml',
        'views/class_views.xml',
        'views/course_views.xml',
        'views/grade_views.xml',
        'views/actions.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}