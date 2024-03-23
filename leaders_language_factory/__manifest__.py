# -*- coding: utf-8 -*-
{
    'name': "leaders_language_factory",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'project', 'crm', 'sale', 'sale_crm', 'account', 'hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/leaders_security.xml',
        'views/account_move_inherited.xml',
        'views/crm_lead_inherited.xml',
        'wizard/sales_project_notes.xml',
        'views/sale_order_inherited.xml',
        'wizard/change_request_reason.xml',
        'views/project_inherited.xml',
        'views/menu_items.xml',
        'wizard/crm_lead_lost_inherited.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'web.assets_backend': ['leaders_language_factory/static/src/js/leaders.js']
        , },
    'installable': True,
    'application': True,
}
