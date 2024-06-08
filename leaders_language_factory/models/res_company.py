
from odoo import fields, models


class ResCompanyInherited(models.Model):
    _inherit = 'res.company'

    sale_tax_id = fields.Many2one('account.tax')

