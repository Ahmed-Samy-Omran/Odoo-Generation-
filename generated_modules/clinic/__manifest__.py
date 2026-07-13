{
    'name': 'clinic',
    'version': '1.0',
    'category': 'Healthcare',
    'summary': 'Clinic module (patients)',
    'author': 'Generated',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/clinic_patient_views.xml',
    ],
    'installable': True,
    'application': False,
}
