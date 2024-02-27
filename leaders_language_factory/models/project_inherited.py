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
    source_attachment_ids = fields.Many2many('ir.attachment', 'project_source_attachment_rel', string='Source Files')
    target_attachment_ids = fields.Many2many('ir.attachment', relation='project_target_attachment_rel',
                                             string='Target Files')

    proofreader_attachment_ids = fields.Many2many('ir.attachment', relation='project_final_attachment_rel',
                                                  string='Final Files')
    quality_attachment = fields.Many2many('ir.attachment', relation='project_quality_attachment_rel',
                                          string='Quality Document')

    def _check_is_project_manager(self):
        if self.env.user.has_group('project.group_project_manager'):
            print('yes')
            self.is_project_manager = True
        else:
            print('No')
            self.is_project_manager = False


class ProjectTaskInherited(models.Model):
    _inherit = 'project.task'

    is_project_manager = fields.Boolean(compute='_check_is_project_manager')
    num_of_words = fields.Integer(string="Number of words")
    source_attachment_ids = fields.Many2many('ir.attachment', relation='task_source_attachment_rel',
                                             string='Source Files', readonly='1')

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

    @api.onchange('user_ids')
    def onchange_user_ids(self):
        self.change_request_reason = ' <br> '

    def _check_is_project_manager(self):
        if self.env.user.has_group('project.group_project_manager'):
            self.is_project_manager = True
        else:
            self.is_project_manager = False

    def create(self, vals):
        record = super(ProjectTaskInherited, self).create(vals)

        record.source_attachment_ids = record.project_id.source_attachment_ids.ids

        return record

    def write(self, vals):

        if ('state' in vals and vals['state'] == '02_changes_requested'
                and 'change_request_reason' not in vals and (is_html_empty(self.change_request_reason))):

            raise ValidationError('Please enter your refuse reason')

        else:
            return super(ProjectTaskInherited, self).write(vals)


class ProjectTargetAttachmentRel(models.Model):
    _name = 'project.target.attachment.rel'

    project_project_id = fields.Many2one('project.project')
    ir_attachment_id = fields.Many2one('ir.attachment')



class ProjectSourceAttachmentRel(models.Model):
    _name = 'project.source.attachment.rel'
    project_project_id = fields.Many2one('project.project')
    ir_attachment_id = fields.Many2one('ir.attachment')



class ProjectQualityAttachmentRel(models.Model):
    _name = 'project.quality.attachment.rel'
    project_project_id = fields.Many2one('project.project')
    ir_attachment_id = fields.Many2one('ir.attachment')


class ProjectFinalAttachmentRel(models.Model):
    _name = 'project.final.attachment.rel'
    project_project_id = fields.Many2one('project.project')
    ir_attachment_id = fields.Many2one('ir.attachment')


class TaskSourceAttachmentRel(models.Model):
    _name = 'task.source.attachment.rel'
    project_task_id = fields.Many2one('project.task')
    ir_attachment_id = fields.Many2one('ir.attachment')


class TaskTargetAttachmentRel(models.Model):
    _name = 'task.target.attachment.rel'
    project_task_id = fields.Many2one('project.task')
    ir_attachment_id = fields.Many2one('ir.attachment')
