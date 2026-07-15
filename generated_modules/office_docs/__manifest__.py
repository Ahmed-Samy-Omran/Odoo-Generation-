# -*- coding: utf-8 -*-
{
    'name': 'office_docs',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'A minimal document management module for small offices to track and organize documents such as contracts, invoices, and receipts with basic status workflows.',
    'author': 'Generated Module',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/office_document_views.xml',
        'views/actions.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}