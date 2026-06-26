# -*- coding: utf-8 -*-
{
    'name': 'project_task_management',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Advanced project task management with time tracking and reporting',
    'author': 'Generated Module',
    'depends': ['base', 'project', 'hr_timesheet', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/project_task_management_task_views.xml',
        'views/actions.xml',
        'views/menus.xml',
        'reports/project_task_management_task_report_report.xml',
        'reports/project_task_management_task_report_template.xml',
    ],
    'installable': True,
    'application': False,
}