from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import is_html_empty
import logging
from odoo import _

_logger = logging.getLogger(__name__)

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

    source_attachment_ids = fields.Many2many('ir.attachment', 'project_source_attachment_rel',
                                             column1='project_id', column2='attachment_id', string='Source Files',
                                             readonly='1')
    proofreader_target_attachment_ids = fields.Many2many('ir.attachment', relation='project_target_attachment_rel',
                                                         column1='project_id', column2='attachment_id',
                                                         string='Proofreader Target Files')
    translator_target_attachment_ids = fields.Many2many('ir.attachment',
                                                        relation='project_translator_target_attachment_rel',
                                                        column1='project_id', column2='attachment_id',
                                                        string='Translator Target Files')

    quality_attachment = fields.Many2many('ir.attachment', relation='project_quality_attachment_rel',
                                          column1='project_id', column2='attachment_id'
                                          , string='Quality Document')

    detailed_timeline = fields.Text(string='Detailed Timeline', readonly=True)
    product_ids = fields.Many2many('product.product', relation='product_project_rel',
                                   column1='project_id', column2='product_id', string="services", readonly=True)
    source_language = fields.Many2one('res.lang', string='Source Language',
                                      domain="['|',('active', '=', False),('active', '=', True)  ]", readonly='True')
    target_language = fields.Many2one('res.lang', string='Target Language'
                                      , domain="['|',('active', '=', False),('active', '=', True)  ]", readonly='True')
    sale_line_id = fields.Many2one(
        'sale.order.line', 'Sales Order Item', copy=False,
        sudo_compute="true")

    def _get_default_type_common(self):
        ids = self.env["project.task.type"].search([("case_default", "=", True)])
        return ids

    type_ids = fields.Many2many(default=lambda self: self._get_default_type_common())

    def _check_is_project_manager(self):

        if self.env.user.has_group('project.group_project_manager'):
            self.is_project_manager = True
        else:
            self.is_project_manager = False

    def create(self, vals):
        record = super(ProjectProjectInherited, self).create(vals)
        if record.sale_line_id.order_id:
            record.sale_line_id.order_id.sudo().related_project = record.id
            sale_order_source_attachments = record.sale_line_id.order_id.source_attachment_ids
            record.source_attachment_ids = get_duplicated_attachment(record, sale_order_source_attachments)
            if record.sale_line_id.order_id.order_line:
                record.source_language = record.sale_line_id.order_id.order_line[0].source_language.id

                record.target_language = record.sale_line_id.order_id.order_line[0].target_language.id

                for line in record.sale_line_id.order_id.order_line:
                    print(line.product_id)
                    record.sudo().write({'product_ids': [(4, line.product_id.id)]})
            if record.sale_line_id.order_id.opportunity_id:
                record.detailed_timeline = record.sale_line_id.order_id.opportunity_id.detailed_timeline
            # to edit
            project_admin = self.env.ref("project.group_project_manager").users.ids[1]
            if project_admin:
                record.user_id = project_admin

        return record

    def add_target_field_to_sale_order(self):
        if self.proofreader_target_attachment_ids:
            order_target_attachment = get_duplicated_attachment(self.sale_line_id.order_id,
                                                                self.proofreader_target_attachment_ids)
            self.sale_line_id.order_id.sudo().write({'target_attachment_ids': order_target_attachment})
        elif not self.proofreader_target_attachment_ids and self.translator_target_attachment_ids:
            order_target_attachment = get_duplicated_attachment(self.sale_line_id.order_id,
                                                                self.translator_target_attachment_ids)
            self.sale_line_id.order_id.sudo().write({'target_attachment_ids': order_target_attachment})


class ProjectTaskInherited(models.Model):
    _inherit = 'project.task'
    is_project_manager = fields.Boolean(compute='_check_is_project_manager')

    user_ids = fields.Many2many('res.users', relation='project_task_user_rel', column1='task_id', column2='user_id',
                                string='Assignees', context={'active_test': False}, tracking=True,
                                readonly=True)

    num_of_words = fields.Integer(string="Number of words")
    source_attachment_ids = fields.Many2many('ir.attachment', relation='task_translator_source_attachment_rel',
                                             string='Source Files', readonly='1')

    target_attachment_ids = fields.Many2many('ir.attachment', relation='task_target_attachment_rel',
                                             string='Target Files')

    product_ids = fields.Many2many('product.product', related='project_id.product_ids', relation='product_project_rel',
                                   column1='task_id', column2='product_id', string="services", readonly=True)
    source_language = fields.Many2one('res.lang', string='Source Language', related='project_id.source_language',
                                      readonly='True')
    target_language = fields.Many2one('res.lang', string='Target Language'
                                      , related='project_id.target_language', readonly='True')
    task_type = fields.Selection([
        ('0', 'Translation'),
        ('1', 'Proofreading'),
        ('2', 'Editing')
    ], string='Task Type', required='1',
        default='0')

    state = fields.Selection([
        ('01_in_progress', 'Waiting'),
        ('02_changes_requested', 'Changes Requested'),
        ('03_approved', 'Approved'),
        *CLOSED_STATES.items(),
        ('04_waiting_normal', 'Waiting'),
    ])
    change_request_reason = fields.Html(string='Discuss Reason')
    # proofreading fields
    translator_num_of_words = fields.Integer(string="Translator Number of words", readonly=1)

    translator_target_attachment_ids = fields.Many2many('ir.attachment',
                                                        relation='task_translator_target_attachment_rel',
                                                        column1='project_id', column2='attachment_id',
                                                        string='Translator Target Files',
                                                        readonly='!is_project_manager')
    translator_mistakes = fields.Html('Translator Mistakes')
    ##########################
    # editing fields
    edit_notes = fields.Html('Edit Notes')
    edit_attachment_ids = fields.Many2many('ir.attachment',
                                           relation='task_files_attachment_rel',
                                           column1='task_id', column2='attachment_id',
                                           string='Files that need editing')

    ######################

    def create(self, vals):
        record = super(ProjectTaskInherited, self).create(vals)
        if 'task_type' in vals and vals['task_type'] == '1':
            record.move_translator_results_to_proofreader()
        project_source_attachment = record.project_id.source_attachment_ids
        record.source_attachment_ids = get_duplicated_attachment(record, project_source_attachment)
        return record

    @api.model
    def _get_default_personal_stage_create_vals(self, user_id):
        return [
            {'sequence': 1, 'name': _('Running'), 'user_id': user_id, 'fold': False},
            {'sequence': 2, 'name': _('Completed'), 'user_id': user_id, 'fold': False},

        ]

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
        if self.task_type == '1':
            self.move_translator_results_to_proofreader()

    def write(self, vals):
        if ('state' in vals and vals['state'] == '02_changes_requested'
                and 'change_request_reason' not in vals and (is_html_empty(self.change_request_reason))):

            raise ValidationError('Please enter your discuss reason')

        else:
            if 'state' in vals and vals['state'] == '1_done':
                completed_stage = self.env['project.task.type'].sudo().search([('name', '=', 'Completed')])
                vals['stage_id'] = completed_stage.id
                if self.user_ids:
                    for user in self.user_ids:
                        completed_user_stage = self.env['project.task.type'].sudo().search(
                            [('user_id', '=', user.id), ('sequence', '=', '2')], limit=1)

                        if completed_user_stage:
                            vals['personal_stage_type_id'] = completed_user_stage.id
            rec = super(ProjectTaskInherited, self).write(vals)
            if 'state' in vals:

                if vals['state'] == '03_approved':
                    if self.task_type == '0':
                        under_translation_stage = self.env['project.project.stage'].search([
                            ('sequence', '=', 2)])
                        if under_translation_stage:
                            self.project_id.sudo().write({'stage_id': under_translation_stage})
                    if self.task_type == '1':
                        under_proofreading_stage = self.env['project.project.stage'].search([
                            ('sequence', '=', 4)])
                        self.project_id.sudo().write({'stage_id': under_proofreading_stage})
                    if self.task_type == '2':
                        under_editing = self.env['project.project.stage'].search([
                            ('sequence', '=', 5)])
                        self.project_id.sudo().write({'stage_id': under_editing})

                if vals['state'] == '1_done':

                    if self.task_type == '0':
                        project_translator_target_attachments = get_duplicated_attachment(self.project_id,
                                                                                          self.target_attachment_ids)
                        self.project_id.sudo().write(
                            {'translator_target_attachment_ids': [(6, 0, project_translator_target_attachments)]})

                        translation_completed_stage = self.env['project.project.stage'].search([
                            ('sequence', '=', 3)])
                        self.project_id.sudo().write({'stage_id': translation_completed_stage})

                    if self.task_type == '1':
                        project_proofreader_target_attachments = get_duplicated_attachment(self.project_id,
                                                                                           self.target_attachment_ids)
                        self.project_id.sudo().write(
                            {'proofreader_target_attachment_ids': [(6, 0, project_proofreader_target_attachments)]})

                        done_stage = self.env['project.project.stage'].search([
                            ('sequence', '=', 6)])
                        self.project_id.sudo().write({'stage_id': done_stage})

            return rec

    def move_translator_results_to_proofreader(self):
        translation_task = self.env['project.task'].search(
            [('project_id', '=', self.project_id.id), ('task_type', '=', '0'), ('state', '=', '1_done')], limit=1)
        if translation_task:
            self.translator_num_of_words = translation_task.num_of_words
            self.translator_target_attachment_ids = translation_task.target_attachment_ids


class ProjectTaskType(models.Model):
    _inherit = "project.task.type"

    case_default = fields.Boolean(
        string="Default for New Projects",
        help="If you check this field, this stage will be proposed by default "
             "on each new project. It will not assign this stage to existing "
             "projects.",
    )


def get_duplicated_attachment(self, attachments):
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
    return created_attachment_ids
