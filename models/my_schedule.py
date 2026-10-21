from from odoo import api, fields, models, _



class MySchedule:
    _name = "hr.employee.shift.myschedule"
    _description = "My Schedule"

    name = fields.Char('Event Name', required=True)
    start_date = fields.Datetime('Start', required=True)
    stop_date = fields.Datetime('Stop')

    record_ref = fields.Reference(
        selection=[
            ('hr.shift.schedule', 'Shift'), 
        ],
        string="Source Record",
        readonly=True
    )

