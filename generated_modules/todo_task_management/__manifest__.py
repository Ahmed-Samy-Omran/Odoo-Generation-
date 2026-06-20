# -*- coding: utf-8 -*-
{
    'name': 'todo_task_management',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'A simple module for managing todo tasks.',
    'author': 'Generated Module',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/todo_task_management_todo_task_views.xml',
        'views/actions.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}