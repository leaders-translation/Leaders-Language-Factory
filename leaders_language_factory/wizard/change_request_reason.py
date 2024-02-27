# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from markupsafe import Markup
from odoo import api, fields, models, _
from odoo.tools.mail import is_html_empty


class ChangeRequestReason(models.TransientModel):
    _name = 'change.request.reason'
    _description = 'Get Change Request Reason'

    task_id = fields.Many2one('project.task', string='Tasks')

    change_request_reason = fields.Html(
        'Refuse Reason', required=True
    )

    @api.model
    def default_get(self, fields):
        res = super(ChangeRequestReason, self).default_get(fields)
        if not res.get('task_id') and self._context.get('active_id'):
            res['task_id'] = self._context['active_id']
        return res

    def action_refuse_task(self):
        """Mark lead as lost and apply the loss reason"""
        self.ensure_one()
        if not is_html_empty(self.change_request_reason):
            self.task_id.change_request_reason = self.change_request_reason
            self.task_id.state = "02_changes_requested"
        return self.task_id
