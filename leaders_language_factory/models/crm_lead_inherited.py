from odoo import models, fields, api

AVAILABLE_TIMELINE = [
    ('1', 'Normal'),
    ('2', 'Urgent'),
    ('3', 'Top Urgent'),
]


class CrmLeadInherited(models.Model):
    _inherit = 'crm.lead'

    is_interpretation = fields.Boolean(string='Is Interpretation')
    # common fields
    detailed_timeline = fields.Text(string='Detailed Timeline')
    priority = fields.Selection(AVAILABLE_TIMELINE
                                , string='Timeline', index=True,
                                default=AVAILABLE_TIMELINE[0][0])
    partner_company_type = fields.Char(compute='_compute_partner_company_type', string='Customer Type'
                                       , readonly=True, store=True)

    # interpretation fields
    interpretation_type = fields.Selection([('0', 'Simultaneous'), ('1', 'Consecutive')],
                                           string="Interpretation Type")
    requirements = fields.Selection([('0', 'Booth'), ('1', 'Headset')],
                                    string="others")
    event_name = fields.Char(string='Event Name')
    event_location = fields.Char(string='Event Location')
    days_number = fields.Integer(string='Number of Days')
    event_duration = fields.Integer(string='Event Duration')
    event_date = fields.Datetime(string='Event Date')
    attendees_number = fields.Integer(string='Attendees Number')
    discussed_topics = fields.Text(string='Topics to be Discussed')
    is_broadcasting_needed = fields.Boolean(string='Broadcasting Needed')
    hotel_ballroom_number = fields.Integer(string='Hotel Ballroom Number')
    required_interpreters_number = fields.Integer(string='Required Interpreters Number')
    technicians_number = fields.Integer(string='Technicians Number')
    # booths_number = fields.Integer(string='Booths Number')
    # headsets_number = fields.Integer(string='Headsets Number')
    interpreter_lines = fields.One2many('interpreter.line', 'lead_id', string='Interpreters')
    interpreter_counts = fields.Integer(readonly='1', compute='_compute_interpreter_count')

    # additional_devices = fields.Char(string='Additional devices')

    @api.depends('partner_id.company_type')
    def _compute_partner_company_type(self):
        for lead in self:
            if lead.partner_id.company_type:
                lead.partner_company_type = 'Individual' if lead.partner_id.company_type == 'person' else 'Company'

    @api.depends('interpreter_lines')
    def _compute_interpreter_count(self):
        for lead in self:
            lead.interpreter_counts = self.env['interpreter.line'].search_count([('lead_id', '=', lead.id)])


class InterpreterLine(models.Model):
    _name = "interpreter.line"
    interpreter_name = fields.Many2one('hr.employee', string="Interpreter", required='1')
    rate = fields.Float(string="Rate")
    lead_id = fields.Many2one('crm.lead')
