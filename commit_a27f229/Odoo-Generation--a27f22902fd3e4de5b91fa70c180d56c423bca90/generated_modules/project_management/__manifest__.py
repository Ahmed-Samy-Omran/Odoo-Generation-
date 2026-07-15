# -*- coding: utf-8 -*-
{
    'name': 'project_management',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Comprehensive project management system with tasks, milestones, and team collaboration',
    'author': 'Generated Module',
    'depends': ['base', 'mail', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/project_management_project_views.xml',
        'views/project_management_task_views.xml',
        'views/project_management_milestone_views.xml',
        'views/actions.xml',
        'views/menus.xml',
        'reports/project_management_reportproject_summary_report.xml',
        'reports/project_management_reportproject_summary_template.xml',
    ],
    'installable': True,
    'application': False,
}