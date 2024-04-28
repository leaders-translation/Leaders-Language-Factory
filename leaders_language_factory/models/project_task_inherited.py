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


class ProjectTaskInherited(models.Model):
    _inherit = 'project.task'
    is_project_manager = fields.Boolean(compute='_check_is_project_manager')

    user_ids = fields.Many2many('res.users', relation='project_task_user_rel', column1='task_id', column2='user_id',
                                string='Assignees', context={'active_test': False}, tracking=True,
                                readonly=True)

    source_attachment_ids = fields.Many2many('ir.attachment', relation='task_translator_source_attachment_rel',
                                             string='Source Files', readonly='1')

    product_id = fields.Many2one('product.product', string="Service", readonly=True)
    source_language = fields.Many2one('res.lang', string='Source Language',
                                      readonly='True')
    target_language = fields.Many2one('res.lang', string='Target Language', readonly='True')

    state = fields.Selection([
        ('01_in_progress', 'Waiting'),
        ('02_changes_requested', 'Changes Requested'),
        ('03_approved', 'Approved'),
        *CLOSED_STATES.items(),
        ('04_waiting_normal', 'Waiting'),
    ])
    change_request_reason = fields.Html(string='Discuss Reason')

    translator_num_of_words = fields.Integer(string="Translator Number of words")

    translator_target_attachment_ids = fields.Many2many('ir.attachment',
                                                        relation='task_translator_target_attachment_rel',
                                                        column1='project_id', column2='attachment_id',
                                                        string='Translator Target Files',

                                                        )
    proofreader_num_of_words = fields.Integer(string="Proofreader Number of words")

    proofreader_target_attachment_ids = fields.Many2many('ir.attachment',
                                                         relation='task_proofreader_target_attachment_rel',
                                                         column1='task_id', column2='attachment_id',
                                                         string='Proofreader Target Files',
                                                         )
    translator_mistakes = fields.Html('Translator Mistakes')
    ##########################
    # editing fields
    edit_notes = fields.Html('Edit Notes')
    edit_attachment_ids = fields.Many2many('ir.attachment',
                                           relation='task_files_attachment_rel',
                                           column1='task_id', column2='attachment_id',
                                           string='Files that need editing')
    phase = fields.Selection([
        ('translation', 'translation'),
        ('proofreading', 'proofreading'),
        ('editing', 'editing')], compute='_compute_phase_from_stage', store=True)

    @api.model
    def _get_default_personal_stage_create_vals(self, user_id):
        return [
            {'sequence': 1, 'name': _('Translation'), 'user_id': user_id, 'fold': False},
            {'sequence': 2, 'name': _('Translation Completed'), 'user_id': user_id, 'fold': False},
            {'sequence': 3, 'name': _('Proofreading'), 'user_id': user_id, 'fold': False},
            {'sequence': 4, 'name': _('Proofreading Completed'), 'user_id': user_id, 'fold': False},
            {'sequence': 5, 'name': _('Editing'), 'user_id': user_id, 'fold': False},
        ]

    @api.onchange('user_ids')
    def onchange_user_ids(self):
        self.change_request_reason = ' <br> '
        self.state = '01_in_progress'

    @api.depends('stage_id')
    def _compute_phase_from_stage(self):
        for rec in self:
            if 5 > rec.stage_id.sequence > 2:
                rec.phase = 'proofreading'
            elif rec.stage_id.sequence == 5:
                rec.phase = 'editing'
            else:
                rec.phase = 'translation'

    def _check_is_project_manager(self):
        if self.env.user.has_group('project.group_project_manager'):
            self.is_project_manager = True
        else:
            self.is_project_manager = False

    def write(self, vals):

        if ('state' in vals and vals['state'] == '02_changes_requested'
                and 'change_request_reason' not in vals and (is_html_empty(self.change_request_reason))):

            raise ValidationError('Please enter your discuss reason')

        else:
            if 'state' in vals and vals['state'] == '1_done':
                self.change_task_stage(vals)

            rec = super(ProjectTaskInherited, self).write(vals)
            self.check_project_stage(vals)
            return rec

    def add_target_files_to_sale_order_line(self):

        if self.proofreader_target_attachment_ids:
            order_target_attachment = get_duplicated_attachment(self.sale_line_id,
                                                                self.proofreader_target_attachment_ids)
            self.sale_line_id.sudo().write({'target_attachment_ids': order_target_attachment})
            self.send_message_to_salesperson()


        elif not self.proofreader_target_attachment_ids and self.translator_target_attachment_ids:
            order_target_attachment = get_duplicated_attachment(self.sale_line_id,
                                                                self.translator_target_attachment_ids)
            self.send_message_to_salesperson()

            self.sale_line_id.sudo().write({'target_attachment_ids': order_target_attachment})
        else:
            raise ValidationError('No target files yet')

    def send_message_to_salesperson(self):
        self.sale_order_id.sudo().message_post(body=self.name + ' is completed and it\'s target files is assigned.',
                                               subject='Project / Sales Notes',
                                               author_id=self.project_id.user_id.partner_id.id,
                                               message_type='comment',
                                               subtype_xmlid='mail.mt_comment')

    def change_task_stage(self, vals):
        if self.stage_id.is_translation:
            trans_completed_stage = self.env['project.task.type'].sudo().search(
                [('name', '=', 'Translation Completed'), ('sequence', '=', '2')], limit=1)
            vals['stage_id'] = trans_completed_stage.id
        elif self.stage_id.is_proofreading:
            proof_completed_stage = self.env['project.task.type'].sudo().search(
                [('name', '=', 'Proofreading Completed'), ('sequence', '=', '4')], limit=1)
            vals['stage_id'] = proof_completed_stage.id

        if self.user_ids:
            for user in self.user_ids:
                completed_user_stage = self.env['project.task.type'].sudo().search(
                    [('user_id', '=', user.id), ('sequence', '=', '2')], limit=1)

                if completed_user_stage:
                    vals['personal_stage_type_id'] = completed_user_stage.id

    def check_project_stage(self, vals):
        if 'state' in vals and vals['state'] == '03_approved':
            if self.project_id and self.project_id.sudo().stage_id.name == 'New':
                under_translation_stage = self.env['project.project.stage'].sudo().search(
                    [('name', '=', 'Under Translation')], limit=1)

                self.project_id.sudo().write({'stage_id': under_translation_stage.id})
        if 'stage_id' in vals:
            if (self.sale_line_id):
                self.sale_line_id.sudo().write({'service_status': self.stage_id.name})
            count = 0
            if self.stage_id.is_proofreading and self.project_id:
                for task in self.project_id.sudo().tasks:
                    if task.stage_id.sequence > 2 and task.stage_id.sequence != 5:
                        count += 1
                if count == len(self.project_id.sudo().tasks):
                    under_proofreading_stage = self.env['project.project.stage'].sudo().search(
                        [('name', '=', 'Under Proofreading')], limit=1)
                    self.project_id.sudo().write({'stage_id': under_proofreading_stage.id})


class ProjectTaskType(models.Model):
    _inherit = "project.task.type"

    case_default = fields.Boolean(
        string="Default for New Projects",
        help="If you check this field, this stage will be proposed by default "
             "on each new project. It will not assign this stage to existing "
             "projects.",
    )
    is_translation = fields.Boolean(string="Is Translation")
    is_proofreading = fields.Boolean(string="Is Proofreading")
    is_editing = fields.Boolean(string="Is Editing")


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
