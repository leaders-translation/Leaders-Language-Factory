from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    quotation_type = fields.Selection([('0', 'General'), ('1', 'Project')],
                                      string="Quotation Type", default='1', required='1')
    is_interpretation = fields.Boolean(string='Is Interpretation', related='opportunity_id.is_interpretation',
                                       readonly=True)
    branch = fields.Selection([('0', 'UAE'), ('1', 'Jordan')],
                              string="Branch", required='1')
    delivery_type = fields.Selection([('0', 'Soft Copy'), ('1', 'Printed or E-copy')],
                                     string="Delivery Type")
    used_papers = fields.Integer(string="Used Papers")


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    estimated_number_of_pages = fields.Integer(string="No. of pages")
    estimated_number_of_words = fields.Integer(string="No. of words")

    source_language = fields.Many2one('res.lang', string='Source',
                                      domain="['|',('active', '=', False),('active', '=', True)  ]")
    target_language = fields.Many2one('res.lang', string='Target'
                                      , domain="['|',('active', '=', False),('active', '=', True)  ]")

    period_in_days = fields.Integer(string='Period | Days')
    no_of_interpreters = fields.Integer(string='No. Interpreters')

    description = fields.Char(string='Description')

    def _prepare_invoice_line(self, **optional_value):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_value)

        if self.source_language and self.target_language:
            res.update({'language_pair': self.source_language.name + '-' + self.target_language.name})
        return res
