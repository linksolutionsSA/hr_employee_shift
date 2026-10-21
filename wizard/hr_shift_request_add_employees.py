from odoo import api, fields, models, _


class HrShiftRequestAddEmployees(models.TransientModel):
    _name = "hr.shift.request.add.employees"
    _description = "Add Employees to Shift Request"

    shift_request_id = fields.Many2one(
        "hr.shift.request", string="Shift Request", required=True
    )
    employee_ids = fields.Many2many("hr.employee", string="Employees")
    existing_shift_request_line_ids = fields.Many2many(
        "hr.employee",
        string="Existing Shift Request Line",
        compute="_compute_existing_employees",
        store=False,
    )

    @api.depends("shift_request_id.shift_request_line_ids")
    def _compute_existing_employees(self):
        for rec in self:
            if rec.shift_request_id:
                rec.existing_shift_request_line_ids = (
                    rec.shift_request_id.shift_request_line_ids.mapped("employee_id")
                )
            else:
                rec.existing_shift_request_line_ids = False

    def action_add_employees(self):
        self.ensure_one()
        if not self.employee_ids:
            return

        shift_request_lines = self.env["hr.shift.request.line"]
        existing_employees = self.shift_request_id.shift_request_line_ids.mapped(
            "employee_id"
        )

        for employee in self.employee_ids:
            if employee in existing_employees:
                continue

            shift_request_lines.create(
                {
                    "shift_request_id": self.shift_request_id.id,
                    "employee_id": employee.id,
                    "off_day": self.shift_request_id.default_day_off,
                }
            )

        return {"type": "ir.actions.act_window_close"}
