from odoo import models, fields, api

AVAILABLE_TIMELINE = [
    ('1', 'Normal'),
    ('2', 'Urgent'),
    ('3', 'Top Urgent'),
]


class CrmStageInherited(models.Model):
    _inherit = 'crm.stage'
    is_lost = fields.Boolean(default=False, string='Is Lost Stage')
    is_negotiation = fields.Boolean(default=False, string='Is Negotiation Stage')


class CrmLeadInherited(models.Model):
    _inherit = 'crm.lead'

    source_attachment_ids = fields.Many2many('ir.attachment', 'lead_source_attachment_rel',
                                             column1='lead_id', column2='attachment_id', string='Source Files')

    is_interpretation = fields.Boolean(string='Is Interpretation')
    # common fields
    detailed_timeline = fields.Text(string='Detailed Timeline')

    timeline = fields.Selection(AVAILABLE_TIMELINE
                                , string='Timeline', index=True,
                                default=AVAILABLE_TIMELINE[0][0], required=True)
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

    interpreter_lines = fields.One2many('interpreter.line', 'lead_id', string='Interpreters')
    interpreter_counts = fields.Integer(readonly='1', compute='_compute_interpreter_count')

    additional_devices = fields.Char(string='Additional devices')
    is_lost_stage = fields.Boolean(compute="_compute_is_lost_stage")

    @api.depends('stage_id')
    def _compute_is_lost_stage(self):
        for lead in self:
            lost_stage = self._stage_find(domain=[('is_lost', '=', True)], limit=None)
            print(lost_stage)
            if lead.stage_id == lost_stage:
                lead.is_lost_stage = True
            else:
                lead.is_lost_stage = False

    @api.depends('partner_id.company_type')
    def _compute_partner_company_type(self):
        for lead in self:
            if lead.partner_id.company_type:
                lead.partner_company_type = 'Individual' if lead.partner_id.company_type == 'person' else 'Company'

    @api.depends('interpreter_lines')
    def _compute_interpreter_count(self):
        for lead in self:
            lead.interpreter_counts = self.env['interpreter.line'].search_count([('lead_id', '=', lead.id)])

    def action_set_lost(self, **additional_values):
        res = super(CrmLeadInherited, self).action_set_lost(**additional_values)

        for lead in self:
            lost_stage = self._stage_find(domain=[('is_lost', '=', True)], limit=None)

            if lost_stage:
                lead.write({'stage_id': lost_stage.id, 'active': True})

        return res


class InterpreterLine(models.Model):
    _name = "interpreter.line"
    _description = "Interpreters"
    interpreter_name = fields.Many2one('hr.employee', string="Interpreter", required='1')
    rate = fields.Float(string="Rate")
    lead_id = fields.Many2one('crm.lead')
