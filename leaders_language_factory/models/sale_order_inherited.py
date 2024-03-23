from odoo import models, fields, api


class SaleOrderInherited(models.Model):
    _inherit = 'sale.order'

    is_interpretation = fields.Boolean(string='Is Interpretation', related='opportunity_id.is_interpretation',
                                       readonly=True)
    delivery_type = fields.Selection([('0', 'Soft Copy'), ('1', 'Printed or E-copy')],
                                     string="Delivery Type")
    used_papers = fields.Integer(string="Used Papers")

    source_attachment_ids = fields.Many2many('ir.attachment', related='opportunity_id.source_attachment_ids',
                                             string='Source Files', readonly='1')

    target_attachment_ids = fields.Many2many('ir.attachment', relation='sale_target_attachment_rel',
                                             string='Target Files', readonly='1')
    project_ids = fields.Many2many('project.project', compute_sudo=True)

    def write(self, vals):
        rec = super(SaleOrderInherited, self).write(vals)
        if 'state' in vals and vals['state'] == 'sale':
            self.opportunity_id.stage_id = self.env['crm.stage'].search([('is_won', '=', True)]).id
        return rec

    def create(self, vals):
        rec = super(SaleOrderInherited, self).create(vals)
        nego_stage = self.env['crm.stage'].search([('is_negotiation', '=', True)])
        print(nego_stage)
        if nego_stage:
            rec.opportunity_id.stage_id = nego_stage.id
        return rec

    def action_quotation_download(self):
        pdf, _ = self.env['ir.actions.report'].sudo()._render_qweb_pdf('sale.action_report_saleorder',
                                                                       [self.id])
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', u'%s' % len(pdf))]
        return self.make_response(pdf, headers=pdfhttpheaders)


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

    @api.depends('product_id', 'company_id')
    def _compute_tax_id(self):
        if self.company_id.child_ids:
            uae_tax = self.env['account.tax'].sudo().search([('type_tax_use', '=', 'sale'), ('name', '=', '5%')],
                                                            limit=1)
            if uae_tax:
                self.tax_id = uae_tax
        else:
            jod_tax = self.env['account.tax'].sudo().search([('type_tax_use', '=', 'sale'), ('name', '=', '15%')],
                                                            limit=1)

            if jod_tax:
                self.tax_id = jod_tax
