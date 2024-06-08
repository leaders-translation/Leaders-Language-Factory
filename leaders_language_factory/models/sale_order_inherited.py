from odoo import models, fields


class SaleOrderInherited(models.Model):
    _inherit = 'sale.order'

    is_interpretation = fields.Boolean(string='Is Interpretation', related='opportunity_id.is_interpretation',
                                       readonly=True)
    delivery_type = fields.Selection([('0', 'Soft Copy'), ('1', 'Printed or E-copy')],
                                     string="Delivery Type")
    used_papers = fields.Integer(string="Used Papers")

    project_ids = fields.Many2many('project.project', compute_sudo=True)
    commitment_date = fields.Datetime(related='opportunity_id.detailed_timeline', readonly='1',
                                      string="Detailed Timeline")

    contact_name = fields.Char(related='opportunity_id.contact_name',
                               string="Contact Person")
    related_project = fields.Many2one('project.project')
    project_status = fields.Text(compute='_get_project_stage')

    def _get_project_stage(self):
        for rec in self:
            rec.project_status = ""
            if rec.sudo().related_project:
                rec.project_status = rec.sudo().related_project.stage_id.name

    def write(self, vals):
        rec = super(SaleOrderInherited, self).write(vals)
        if 'state' in vals and vals['state'] == 'sale':
            self.opportunity_id.stage_id = self.env['crm.stage'].search([('is_won', '=', True)]).id

        return rec

    def create(self, vals):
        rec = super(SaleOrderInherited, self).create(vals)
        if (rec.opportunity_id):

            nego_stage = self.env['crm.stage'].search([('is_negotiation', '=', True)])

            if nego_stage:
                rec.opportunity_id.stage_id = nego_stage.id
        return rec

    def action_quotation_download(self):

        return self.env.ref('sale.action_report_saleorder').report_action(self)

    def _compute_sale_order_template_id(self):
        for order in self:
            if order.is_interpretation:
                order_template_id = self.env['sale.order.template'].search([('is_interpretation_template', "=", True)],
                                                                           limit=1)
                order.sale_order_template_id = order_template_id.id
            elif order.partner_id.company_type == 'person':
                order_template_id = self.env['sale.order.template'].search([('is_individual_template', "=", True)],
                                                                           limit=1)
                order.sale_order_template_id = order_template_id.id
            elif order.partner_id.company_type == 'company':
                order_template_id = self.env['sale.order.template'].search([('is_company_template', "=", True)],
                                                                           limit=1)
                order.sale_order_template_id = order_template_id.id

