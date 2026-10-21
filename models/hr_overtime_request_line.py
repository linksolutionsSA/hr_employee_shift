from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError


class HrOvertimeRequestLine(models.Model):
    _name = "hr.overtime.request.line"
    _description = "HR Overtime Request Line"

    name = fields.Char(
        string="Description",
        compute="_compute_name",
        store=True,
        default="Overtime Request Line",
    )

    overtime_request_id = fields.Many2one(
        "hr.overtime.request",
        string="Overtime Request",
        ondelete="cascade",
        readonly=True,
    )
    employee_id = fields.Many2one(
        "hr.employee", string="Employee", required=True, help="Employee"
    )
    cost_of_overtime = fields.Float(
        string="Cost of Overtime",
        default=0.0,
        compute="_compute_cost_of_overtime",
        store=True,
    )

    @api.depends("employee_id", "overtime_request_id")
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.employee_id.name} - {rec.employee_id.barcode}"

    @api.depends(
        "employee_id",
        "overtime_request_id",
        "overtime_request_id.total_overtime_hours",
    )
    def _compute_cost_of_overtime(self):
        for rec in self:
            cost_per_hour = rec._get_overtime_cost_per_hour()
            rec.cost_of_overtime = cost_per_hour

    # ------------- helper functions -------------
    def _get_overtime_cost_per_hour(self):
        try:
            ot_rule_code = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("hr_employee_shift.overtime_rule_code")
            )

            ot_rule = self.env["hr.salary.rule"].search(
                [("code", "=", ot_rule_code)], limit=1
            )
            ot_rule_parsed = ot_rule.amount_python_compute.replace(
                "worked_days." + ot_rule_code + ".number_of_hours", "overtime_hours"
            )
            localdict = {
                "contract": self.employee_id.contract_id,
                "overtime_hours": self.overtime_request_id.total_overtime_hours,
                "result": 0.0,
            }

            for rec in self:
                safe_eval(
                    ot_rule_parsed,
                    localdict,
                    mode="exec",
                    nocopy=True,
                )
            return localdict["result"]
        except Exception as e:
            return 0.0
            raise UserError(
                _("Failed to calculate overtime cost per hour.\n ERROR: %s" % e)
            ) from e
