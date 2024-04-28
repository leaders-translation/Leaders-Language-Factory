from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


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

    detailed_timeline = fields.Text(string='Detailed Timeline', readonly=True)

    sale_line_id = fields.Many2one(
        'sale.order.line', 'Sales Order Item', copy=False,
        sudo_compute="true")

    target_source_pairs = fields.Html(compute='_compute_target_source_pairs')

    def _get_default_type_common(self):
        ids = self.env["project.task.type"].search([("case_default", "=", True)])
        return ids

    type_ids = fields.Many2many(default=lambda self: self._get_default_type_common())

    def _check_is_project_manager(self):

        if self.env.user.has_group('project.group_project_manager'):
            self.is_project_manager = True
        else:
            self.is_project_manager = False

    def _compute_target_source_pairs(self):

        for rec in self:
            rec.target_source_pairs = ''

            for task in rec.tasks:
                if task.source_language and task.target_language:
                    rec.target_source_pairs = rec.target_source_pairs + task.source_language.name + ' => ' + task.target_language.name

    def create(self, vals):
        record = super(ProjectProjectInherited, self).create(vals)
        if record.sale_line_id.order_id:
            record.sale_line_id.order_id.sudo().related_project = record.id

            if record.sale_line_id.order_id.opportunity_id:
                record.detailed_timeline = record.sale_line_id.order_id.opportunity_id.detailed_timeline
            # to edit
            project_admin = self.env.ref("project.group_project_manager").users.ids[1]
            if project_admin:
                record.user_id = project_admin

        return record


def get_duplicated_attachment(record, attachments):
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
