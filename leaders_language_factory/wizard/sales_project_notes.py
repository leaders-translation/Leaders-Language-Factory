# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from markupsafe import Markup
from odoo import api, fields, models, _
from odoo.tools.mail import is_html_empty


class SalesProjectNotes(models.TransientModel):
    _name = 'sales.project.notes'
    _description = 'notes between salesperson and project manager'

    project_id = fields.Many2one('project.project')

    sale_order_id = fields.Many2one('sale.order')

    note = fields.Html(
        'Note', required=True
    )
    attachment_ids = fields.Many2many('ir.attachment', 'project_sale_attachment_rel',
                                      column1='project_id', column2='sale_id', string="Attachments")
    sender_id = fields.Many2one('res.users', string='sender')

    @api.model
    def default_get(self, fields):
        res = super(SalesProjectNotes, self).default_get(fields)

        if self._context['active_model'] == 'sale.order':
            if not res.get('sale_order_id') and self._context.get('active_id'):
                res['sale_order_id'] = self._context['active_id']
                res['sender_id'] = self.env['sale.order'].sudo().search(
                    [('id', '=', self._context['active_id'])]).user_id.id
        elif self._context['active_model'] == 'project.project':
            if not res.get('project_id') and self._context.get('active_id'):
                res['project_id'] = self._context['active_id']
                res['sender_id'] = self.env['project.project'].sudo().search(
                    [('id', '=', self._context['active_id'])]).user_id.id

        return res

    def action_send_note(self):
        self.ensure_one()
        if not is_html_empty(self.note):
            if self._context['active_model'] == 'sale.order':
                for project_id in self.sale_order_id.sudo().project_ids:
                    project_id.sudo().message_post(body=self.note,
                                                   author_id=self.sender_id.partner_id.id,
                                                   subject='Project / Sales Notes',
                                                   message_type='comment',
                                                   subtype_xmlid='mail.mt_comment',
                                                   attachment_ids=self.attachment_ids.ids)
                self.sale_order_id.sudo().message_post(body=self.note,
                                                       subject='Project / Sales Notes',
                                                       author_id=self.sender_id.partner_id.id,
                                                       message_type='comment',
                                                       subtype_xmlid='mail.mt_comment',
                                                       attachment_ids=self.attachment_ids.ids)

            elif self._context['active_model'] == 'project.project':
                self.project_id.sudo().sale_line_id.order_id.sudo().message_post(body=self.note,
                                                                                 author_id=self.sender_id.partner_id.id,
                                                                                 subject='Project / Sales Notes',
                                                                                 message_type='comment',
                                                                                 subtype_xmlid='mail.mt_comment',
                                                                                 attachment_ids=self.attachment_ids.ids)

                self.project_id.sudo().message_post(body=self.note,
                                                    author_id=self.sender_id.partner_id.id,
                                                    subject='Project / Sales Notes',
                                                    message_type='comment',
                                                    subtype_xmlid='mail.mt_comment',
                                                    attachment_ids=self.attachment_ids.ids)
