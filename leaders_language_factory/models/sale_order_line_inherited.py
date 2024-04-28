from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    estimated_number_of_pages = fields.Integer(string="No. of pages")
    estimated_number_of_words = fields.Integer(string="No. of words")

    source_language = fields.Many2one('res.lang', string='Source',
                                      domain="['|',('active', '=', False),('active', '=', True)  ]")
    target_language = fields.Many2one('res.lang', string='Target'
                                      , domain="['|',('active', '=', False),('active', '=', True)  ]")

    source_attachment_ids = fields.Many2many('ir.attachment', 'sale_line_source_attachment_rel',
                                             column1='order_line', column2='attachment_id', string='Source Files')

    target_attachment_ids = fields.Many2many('ir.attachment', 'sale_line_target_attachment_rel',
                                             column1='order_line', column2='attachment_id', string='Target Files', readonly=1)

    period_in_days = fields.Integer(string='Period | Days')
    no_of_interpreters = fields.Integer(string='No. Interpreters')

    description = fields.Char(string='Description')
    service_status = fields.Text(readonly=1)

    def _prepare_invoice_line(self, **optional_value):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_value)

        if self.source_language and self.target_language:
            res.update({'language_pair': self.source_language.name + '-' + self.target_language.name})
        return res

    def _timesheet_create_task_prepare_values(self, project):

        values = super(SaleOrderLine, self)._timesheet_create_task_prepare_values(project)

        values.update({
            'product_id': self.product_id.id,
            'source_language': self.source_language.id,
            'target_language': self.target_language.id,

        }
        )
        return values

    def _timesheet_create_task(self, project):
        task = super(SaleOrderLine, self)._timesheet_create_task(project)
        print(task)
        if self.source_attachment_ids:
            sol_source_attachments = get_duplicated_attachment(task, self.source_attachment_ids)
            print(sol_source_attachments)
            task.write({'source_attachment_ids': [(6, 0, sol_source_attachments)]})
        return task

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


def get_duplicated_attachment(record, attachments):
    print(record)
    created_attachment_ids = []

    for attachment in attachments:
        attachment_data = {
            'name': attachment.name,
            'res_name': record.name,
            'type': 'binary',
            'datas': attachment.datas,
            'res_model': record._name,
            'res_id': record.id,
        }
        created_attachment = record.env['ir.attachment'].sudo().create(attachment_data)
        created_attachment_ids.append(created_attachment.id)

    # Access the IDs of the created attachments using the created_attachment_ids list
    return created_attachment_ids
