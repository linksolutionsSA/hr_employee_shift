from odoo import api, fields, models


class HrOvertimeSchedule(models.Model):
    _name = "hr.overtime.schedule"
    _description = "HR Overtime Schedule"

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
        help="Employee",
    )
    overtime_request_id = fields.Many2one(
        "hr.overtime.request",
        string="Overtime Request",
        ondelete="cascade",
    )
    state = fields.Selection(
        related="overtime_request_id.state",
        string="Overtime Request State",
    )
    start_date = fields.Date(
        string="Start Date",
        required=True,
        help="Start date of the overtime request",
    )
    end_date = fields.Date(
        string="End Date",
        required=True,
        help="End date of the overtime request",
    )
    overtime_hours = fields.Float(
        string="Overtime Hours Per Day",
        store=True,
        help="Overtime hours per day",
    )
    rel_hr_schedule = fields.Many2one("hr.contract")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    department_id = fields.Many2one(
        "hr.department",
        related="employee_id.department_id",
        string="Department",
        store=True,
    )
    total_overtime_hours = fields.Float(
        string="Total Overtime Hours",
        compute="_compute_total_overtime_hours",
        store=True,
    )
    # design
    name = fields.Char(
        string="Name",
        required=True,
        compute="_compute_name",
        help="Name of the shift schedule",
    )

    @api.depends("start_date", "end_date")
    def _compute_total_overtime_hours(self):
        for record in self:
            if record.start_date and record.end_date:
                record.total_overtime_hours = (
                    (record.end_date - record.start_date).days + 1
                ) * record.overtime_hours
            else:
                record.total_overtime_hours = 0.0

    @api.depends("start_date", "end_date")
    def _compute_name(self):
        for record in self:
            record.name = f"{record.employee_id.name} - {record.overtime_hours} hours"

    @api.model
    def create(self, vals_list):
        contract_id = vals_list.get("rel_hr_schedule")
        contract = self.env["hr.contract"].browse(contract_id)
        vals_list["employee_id"] = contract.employee_id.id
        if not vals_list.get("company_id"):
            vals_list["company_id"] = contract.company_id.id or self.env.company.id
        return super(HrOvertimeSchedule, self).create(vals_list)

    @api.model
    def write(self, vals):
        return super(HrOvertimeSchedule, self).write(vals)
