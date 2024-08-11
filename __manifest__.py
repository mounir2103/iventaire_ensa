{
    'name': 'Inventaire ENSA',
    'version': '1.0',
    'depends': ['base', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}