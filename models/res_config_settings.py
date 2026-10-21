from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Add your new boolean field
    # The 'config_parameter' stores this field's value in 'ir.config_parameter'
    # under the key 'hr_employee_shift.auto_accept'
    shift_auto_accept = fields.Boolean(
        string="Auto-Accept Shifts",
        config_parameter="hr_employee_shift.auto_accept",
        help="When enabled, employee shifts will be auto-accepted.",
    )

    number_of_off_days = fields.Integer(
        string="Number of Off Days",
        config_parameter="hr_employee_shift.number_of_off_days",
        default=1,
        help="Number of off days in a week.",
    )

    max_overtime_per_week = fields.Float(
        string="Maximum Overtime Hours Per Week",
        config_parameter="hr_employee_shift.max_overtime_per_week",
        default=12,
        help="Maximum number of overtime hours allowed per week for an employee.",
    )

    overtime_rule_code = fields.Char(
        string="Overtime Rule Code",
        config_parameter="hr_employee_shift.overtime_rule_code",
        help="Overtime rule code.",
    )

    cutoff_date = fields.Integer(
        string="Cutoff Date",
        config_parameter="hr_employee_shift.cutoff_date",
        default=15,
        help="Cutoff date for shift requests.",
    )

    @api.constrains("cutoff_date")
    def _check_cutoff_date(self):
        for record in self:
            if not (1 <= record.cutoff_date <= 31):
                raise ValidationError("Cutoff date must be between 1 and 31.")
