from odoo import api, fields, models, _


class HrOvertimeRequestAddEmployees(models.TransientModel):
    _name = "hr.overtime.request.add.employees"
    _description = "Add Employees to Overtime Request"

    overtime_request_id = fields.Many2one(
        "hr.overtime.request", string="Overtime Request", required=True
    )
    employee_ids = fields.Many2many("hr.employee", string="Employees")
    existing_employee_ids = fields.Many2many(
        "hr.employee", related="overtime_request_id.existing_overtime_request_line_ids"
    )

    def action_add_employees(self):
        self.ensure_one()
        if not self.employee_ids:
            return

        overtime_request_lines = self.env["hr.overtime.request.line"]
        existing_employees = self.overtime_request_id.overtime_request_line_ids.mapped(
            "employee_id"
        )

        for employee in self.employee_ids:
            if employee in existing_employees:
                continue

            overtime_request_lines.create(
                {
                    "overtime_request_id": self.overtime_request_id.id,
                    "employee_id": employee.id,
                }
            )

        return {"type": "ir.actions.act_window_close"}
