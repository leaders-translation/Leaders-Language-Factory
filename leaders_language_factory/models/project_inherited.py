from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import is_html_empty

CLOSED_STATES = {
    '1_done': 'Done',
    '1_canceled': 'Canceled',
}


class ProjectProjectInherited(models.Model):
    _inherit = 'project.project'
    privacy_visibility = fields.Selection([
        ('followers', 'Invited internal users (private)'),
        ('employees', 'All internal users'),
        ('portal', 'Invited portal users and all internal users (public)'),
    ],
        string='Visibility', required=True,
        default='followers')

    is_project_manager = fields.Boolean(compute='_check_is_project_manager')
    order_delivery_date = fields.Datetime(
        string="Sale Order Delivery Date", readonly='1')
    source_attachment_ids = fields.Many2many('ir.attachment', 'project_source_attachment_rel',
                                             column1='project_id', column2='attachment_id', string='Source Files',
                                             readonly='1')
    target_attachment_ids = fields.Many2many('ir.attachment', relation='project_target_attachment_rel',
                                             column1='project_id', column2='attachment_id',
                                             string='Target Files')

    quality_attachment = fields.Many2many('ir.attachment', relation='project_quality_attachment_rel',
                                          column1='project_id', column2='attachment_id'
                                          , string='Quality Document')

    def _check_is_project_manager(self):

        if self.env.user.has_group('project.group_project_manager'):
            self.is_project_manager = True
        else:
            self.is_project_manager = False

    def create(self, vals):
        record = super(ProjectProjectInherited, self).create(vals)
        if record.sale_line_id.order_id:
            record.order_delivery_date = record.sale_line_id.order_id.commitment_date
            sale_order_source_attachments = record.sale_line_id.order_id.source_attachment_ids
            record.source_attachment_ids = get_duplicated_attachment(record, sale_order_source_attachments)
            project_admin = self.env.ref("project.group_project_manager").users.ids[1]
            if project_admin:
                record.user_id = project_admin

        return record

    def add_target_field_to_sale_order(self):
        order_target_attachment = get_duplicated_attachment(self.sale_line_id.order_id, self.target_attachment_ids)
        self.sale_line_id.order_id.sudo().write({'target_attachment_ids': order_target_attachment})


class ProjectTaskInherited(models.Model):
    _inherit = 'project.task'

    is_project_manager = fields.Boolean(compute='_check_is_project_manager')
    translator_num_of_words = fields.Integer(string="Translator Number of words", readonly=1, invisible='task_type==1')
    num_of_words = fields.Integer(string="Number of words")
    source_attachment_ids = fields.Many2many('ir.attachment', relation='task_translator_source_attachment_rel',
                                             string='Source Files', readonly='1')
    translator_target_attachment_ids = fields.Many2many('ir.attachment',
                                                        relation='task_translator_target_attachment_rel',
                                                        string='Translator Target Files', readonly='1')

    target_attachment_ids = fields.Many2many('ir.attachment', relation='task_target_attachment_rel',
                                             string='Target Files')

    task_type = fields.Selection([
        ('0', 'Translation'),
        ('1', 'Proofreading'),
    ], string='Task Type', required='parent_id',
        default='0')

    state = fields.Selection([
        ('01_in_progress', 'Waiting'),
        ('02_changes_requested', 'Changes Requested'),
        ('03_approved', 'Approved'),
        *CLOSED_STATES.items(),
        ('04_waiting_normal', 'Waiting'),
    ])
    change_request_reason = fields.Html(string='Refuse Reason')
    translation_mistakes = fields.Html(string="Translation Mistakes")

    def create(self, vals):
        record = super(ProjectTaskInherited, self).create(vals)
        project_source_attachment = record.project_id.source_attachment_ids
        record.source_attachment_ids = get_duplicated_attachment(record, project_source_attachment)
        return record

    @api.onchange('user_ids')
    def onchange_user_ids(self):
        self.change_request_reason = ' <br> '
        self.state = '01_in_progress'

    def _check_is_project_manager(self):
        if self.env.user.has_group('project.group_project_manager'):
            self.is_project_manager = True
        else:
            self.is_project_manager = False

    @api.onchange('task_type')
    def onchange_task_type(self):
        translation_task = self.env['project.task'].search(
            [('project_id', '=', self.project_id.id), ('task_type', '=', '0'), ('state', '=', '1_done')])
        if translation_task:
            self.translator_num_of_words = translation_task.num_of_words
            self.translator_target_attachment_ids = translation_task.target_attachment_ids

    def write(self, vals):
        if ('state' in vals and vals['state'] == '02_changes_requested'
                and 'change_request_reason' not in vals and (is_html_empty(self.change_request_reason))):

            raise ValidationError('Please enter your refuse reason')

        else:

            if 'task_type' in vals and vals['task_type'] == '1':
                translation_task = self.env['project.task'].search(
                    [('project_id', '=', self.project_id.id), ('task_type', '=', '0'), ('state', '=', '1_done')])
                if translation_task:
                    vals['translator_num_of_words'] = translation_task.num_of_words
                    vals['translator_target_attachment_ids'] = get_duplicated_attachment(self,
                                                                                         translation_task.target_attachment_ids)

            if 'state' in vals and vals['state'] == '1_done':
                project_target_attachments = get_duplicated_attachment(self.project_id, self.target_attachment_ids)
                self.project_id.sudo().write({'target_attachment_ids': [(6, 0, project_target_attachments)]})

            rec = super(ProjectTaskInherited, self).write(vals)

            return rec


def get_duplicated_attachment(self, attachments):
    print(self)
    created_attachment_ids = []

    for attachment in attachments:
        attachment_data = {
            'name': attachment.name,
            'res_name': self.name,
            'type': 'binary',
            'datas': attachment.datas,
            'res_model': self._name,
            'res_id': self.id,
        }
        created_attachment = self.env['ir.attachment'].sudo().create(attachment_data)
        created_attachment_ids.append(created_attachment.id)

    # Access the IDs of the created attachments using the created_attachment_ids list
    print(created_attachment_ids)
    return created_attachment_ids
