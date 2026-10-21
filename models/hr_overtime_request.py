from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date


class HrOvertimeRequest(models.Model):
    _name = "hr.overtime.request"
    _description = "HR Overtime Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Overtime Request Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
        help="The unique identifier for the overtime request.",
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

    overtime_request_line_ids = fields.One2many(
        "hr.overtime.request.line",
        "overtime_request_id",
        string="Overtime Request Line",
        help="Lines of the overtime request",
    )
    overtime_schedule_ids = fields.One2many(
        "hr.overtime.schedule",
        "overtime_request_id",
        string="Overtime Schedule",
        help="Overtime schedule",
    )
    overtime_hours = fields.Float(
        string="Overtime Hours",
        store=True,
        help="Overtime hours",
    )
    total_overtime_hours = fields.Float(
        string="Total Overtime Hours",
        compute="_compute_total_overtime_hours",
        store=True,
        help="Total overtime hours for all employees in this request",
    )

    approved = fields.Boolean(
        string="Approved",
        compute="_compute_approved",
        store=True,
        help="Indicates if the shift request has been approved",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("to_approve", "To Approve"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="draft",
        string="Status",
        tracking=True,
        help="Status of the overtime request",
    )
    approved_by_id = fields.Many2one(
        "res.users",
        string="Approved By",
        readonly=True,
        help="The user who approved this overtime request",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    @api.onchange("company_id")
    def _onchange_company_id(self):
        self.department_id = False

    department_id = fields.Many2one("hr.department", string="Department")

    calendar_color = fields.Char("calander_color", compute="_compute_calendar_color")
    ## design
    existing_overtime_request_line_ids = fields.Many2many(
        "hr.employee",
        string="Existing overtime Request Line",
        compute="_compute_existing_employees",
        store=True,
    )
    existing_employee_department_ids = fields.Many2many(
        "hr.department",
        string="Existing Employee Departments",
        compute="_compute_existing_employee_departments",
        store=True,
    )

    justification = fields.Text(
        string="Justification",
        required=True,
        help="Justification for the overtime request",
        default="",
    )
    total_cost_of_overtime = fields.Float(
        string="Total Cost of Overtime",
        compute="_compute_total_cost_of_overtime",
        store=True,
    )

    @api.depends(
        "overtime_request_line_ids", "overtime_request_line_ids.cost_of_overtime"
    )
    def _compute_total_cost_of_overtime(self):
        for rec in self:
            rec.total_cost_of_overtime = sum(
                rec.overtime_request_line_ids.mapped("cost_of_overtime")
            )

    @api.depends("start_date", "end_date", "overtime_hours")
    def _compute_total_overtime_hours(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.overtime_hours:
                delta = rec.end_date - rec.start_date
                num_days = delta.days + 1
                rec.total_overtime_hours = num_days * rec.overtime_hours
            else:
                rec.total_overtime_hours = 0.0

    @api.depends("overtime_request_line_ids")
    def _compute_existing_employees(self):
        for rec in self:
            rec.existing_overtime_request_line_ids = (
                rec.overtime_request_line_ids.mapped("employee_id")
            )

    @api.depends("overtime_request_line_ids")
    def _compute_existing_employee_departments(self):
        for rec in self:
            rec.existing_employee_department_ids = rec.overtime_request_line_ids.mapped(
                "employee_id.department_id"
            )

    def action_submit(self):
        self.ensure_one()
        if not self.overtime_request_line_ids:
            raise ValidationError(_("Please add employees before you submit"))
        hr_overtime_schedule_obj = self.env["hr.overtime.schedule"]
        for line in self.overtime_request_line_ids:
            employee = line.employee_id
            hr_overtime_schedule_obj.sudo().create(
                {
                    "start_date": self.start_date,
                    "end_date": self.end_date,
                    "rel_hr_schedule": employee.contract_id.id,
                    "employee_id": employee.id,
                    "overtime_hours": self.overtime_hours,
                    "overtime_request_id": self.id,
                }
            )

        self.write({"state": "to_approve"})

    def action_approve(self):
        self.ensure_one()
        self.write({"state": "approved", "approved_by_id": self.env.user.id})

    def action_reject(self):
        self.ensure_one()
        self.write({"state": "rejected"})

    def action_reset_to_draft(self):
        self.ensure_one()
        self._validate_date_passed()
        self.overtime_schedule_ids.sudo().unlink()
        self.sudo().write({"state": "draft", "approved_by_id": False})

    @api.depends("state")
    def _compute_approved(self):
        for request in self:
            request.approved = request.state == "approved"

    @api.model
    def create(self, vals_list):
        if vals_list.get("name", _("New")) == _("New"):
            company_id = vals_list.get("company_id", self.env.company.id)
            company = self.env["res.company"].browse(company_id)

            sequence_number = self.env["ir.sequence"].next_by_code(
                "hr.overtime.request"
            ) or _("New")

            vals_list["name"] = f"{company.name} Overtime Request / {sequence_number}"
        res = super(HrOvertimeRequest, self).create(vals_list)
        res._validate_overtime_rules()
        return res

    def write(self, vals):
        res = super(HrOvertimeRequest, self).write(vals)
        if any(
            f in vals
            for f in [
                "start_date",
                "end_date",
                "overtime_hours",
                "overtime_request_line_ids",
                "state",
            ]
        ):
            self._validate_overtime_rules()
        return res

    def unlink(self):
        self.overtime_schedule_ids.unlink()
        self.overtime_request_line_ids.unlink()
        return super(HrOvertimeRequest, self).unlink()

    def _compute_calendar_color(self):
        for rec in self:
            if rec.state == "draft":
                rec.calendar_color = "#AAAAAA"
            if rec.state == "to_approve":
                rec.calendar_color = "#AAAA00"
            if rec.state == "approved":
                rec.calendar_color = rec.name
            if rec.state == "rejected":
                rec.calendar_color = "#AA0000"

    def _validate_overtime_rules(self):
        max_overtime_per_week = float(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("hr_employee_shift.max_overtime_per_week", default=0.0)
        )

        if max_overtime_per_week <= 0:
            return

        for rec in self:
            if rec.state not in ["draft", "to_approve", "approved"]:
                continue

            for line in rec.overtime_request_line_ids:
                employee = line.employee_id

                # Determine weeks covered by this request
                current_start = rec.start_date
                match_weeks = {}  # WeekStart -> Hours

                while current_start <= rec.end_date:
                    days_to_last_sunday = (current_start.weekday() - 6) % 7
                    week_start = current_start - relativedelta(days=days_to_last_sunday)
                    week_end = week_start + relativedelta(days=6)

                    overlap_start = max(current_start, week_start)
                    overlap_end = min(rec.end_date, week_end)

                    if overlap_start <= overlap_end:
                        days = (overlap_end - overlap_start).days + 1
                        hours = days * rec.overtime_hours
                        if week_start not in match_weeks:
                            match_weeks[week_start] = 0.0
                        match_weeks[week_start] += hours

                    # Move to next week
                    current_start = week_end + relativedelta(days=1)

                # Validate each week
                for week_start, current_req_hours in match_weeks.items():
                    week_end = week_start + relativedelta(days=6)

                    # Find other relevant requests
                    domain = [
                        ("overtime_request_line_ids.employee_id", "=", employee.id),
                        ("state", "in", ["to_approve", "approved"]),
                        ("id", "!=", rec.id),
                        ("start_date", "<=", week_end),
                        ("end_date", ">=", week_start),
                    ]
                    other_requests = self.search(domain)

                    total_existing_hours = 0.0
                    for other in other_requests:
                        # Need to split other requests by week as well to be precise
                        # Calculate exact overlap of 'other' request with THIS week

                        other_overlap_start = max(other.start_date, week_start)
                        other_overlap_end = min(other.end_date, week_end)

                        if other_overlap_start <= other_overlap_end:
                            days = (other_overlap_end - other_overlap_start).days + 1
                            total_existing_hours += days * other.overtime_hours

                    total_week_hours = current_req_hours + total_existing_hours

                    if total_week_hours > max_overtime_per_week:
                        raise UserError(
                            _(
                                "The overtime request for employee %s exceeds the maximum allowed overtime of %s hours per week.\n"
                                "Week: %s to %s\n"
                                "Requested: %s hours\n"
                                "Existing: %s hours\n"
                                "Total: %s hours"
                            )
                            % (
                                employee.name,
                                max_overtime_per_week,
                                week_start,
                                week_end,
                                current_req_hours,
                                total_existing_hours,
                                total_week_hours,
                            )
                        )

    @api.constrains("overtime_hours")
    def _check_overtime_hours(self):
        for rec in self:
            if rec.overtime_hours <= 0:
                raise UserError(_("Overtime hours must be greater than 0."))

    def _validate_date_passed(self):
        cutoff_date = self._get_cutoff_date()
        for rec in self:
            if rec.start_date <= cutoff_date:
                raise UserError(
                    _(
                        "The start date of the overtime request (%s) is not allowed. You cannot modify overtime request after the cutoff date."
                    )
                    % rec.start_date
                )

    def _get_cutoff_date(self):
        current_month = date.today().month
        current_year = date.today().year
        cerrent_day = date.today().day
        cutoff_date_settings = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("hr_employee_shift.cutoff_date")
        )
        cutoff_date_settings = int(cutoff_date_settings)
        if cerrent_day < cutoff_date_settings:
            current_month -= 1
            if current_month == -1:
                current_month = 12
                current_year -= 1

        return date(current_year, current_month, cutoff_date_settings)
