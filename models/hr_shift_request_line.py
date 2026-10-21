from odoo import api, fields, models, _


class HrShiftRequestLine(models.Model):
    _name = "hr.shift.request.line"
    _description = "HR Shift Request Line"

    name = fields.Char(
        string="Description",
        compute="_compute_name",
        store=True,
        default="Potatos",
    )
    shift_request_id = fields.Many2one(
        "hr.shift.request", string="Shift Request", ondelete="cascade", readonly=True
    )
    employee_id = fields.Many2one(
        "hr.employee", string="Employee", required=True, help="Employee"
    )
    off_day = fields.Selection(
        [
            ("saturday", "Saturday"),
            ("sunday", "Sunday"),
            ("monday", "Monday"),
            ("tuesday", "Tuesday"),
            ("wednesday", "Wednesday"),
            ("thursday", "Thursday"),
            ("friday", "Friday"),
        ],
        default="friday",
        string="Off Day",
        help="Off day for the employee",
        required=True,
    )

    @api.depends("employee_id", "off_day")
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.off_day.capitalize()} - {rec.employee_id.name} - {rec.employee_id.barcode}"
