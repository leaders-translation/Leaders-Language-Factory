from odoo import fields, models

class SaleOrderTemplate(models.Model):
    _inherit = 'sale.order.template'

    is_interpretation_template = fields.Boolean(string='Is Interpretation Template')
    is_company_template = fields.Boolean(string='Is Company Template')
    is_individual_template = fields.Boolean(string='Is Individual Template')
