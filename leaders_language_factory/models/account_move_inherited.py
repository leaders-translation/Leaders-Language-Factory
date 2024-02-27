from odoo import models, fields, api


class AccountMoveInherited(models.Model):
    _inherit = 'account.move'

    due_date = fields.Date(string='Due Date')
    delivery_date = fields.Datetime()
    customer_notes = fields.Html(string='Customer Notes')


class AccountMoveLineInherited(models.Model):
    _inherit = 'account.move.line'

    language_pair = fields.Char(readonly=True)

    timeline = fields.Date()
