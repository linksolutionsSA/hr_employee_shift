from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HrShiftRequest(models.Model):
    _name = "hr.shift.request"
    _description = "HR Shift Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    # core
    name = fields.Char(
        string="Shift Requst Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
        help="The unique identifier for the shift request.",
    )
    start_date = fields.Date(
        string="Start Date",
        required=True,
        help="Start date of the shift request",
    )
    end_date = fields.Date(
        string="End Date",
        required=True,
        help="End date of the shift request",
    )
    approved = fields.Boolean(
        string="Approved",
        compute="_compute_approved",
        store=True,
        help="Indicates if the shift request has been approved",
    )
    state = fields.Selection(
        string="State",
        selection=[
            ("draft", "Draft"),
            ("to_approve", "To Approve"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="draft",
        tracking=True,
        help="The status of the shift request",
    )
    request_type = fields.Selection(
        selection=[
            ("assign", "Assign Shift"),
            ("change", "Change Shift"),
        ],
        default=False,
        required=True,
        help="Type of shift request",
    )
    # relations
    shift_id = fields.Many2one(
        "resource.calendar",
        string="Shift",
        required=True,
        help="Shift schedule requested",
    )
    approved_by_id = fields.Many2one(
        "res.users",
        string="Approved By",
        readonly=True,
        help="The user who approved this shift request",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    department_id = fields.Many2one("hr.department", string="Department")
    shift_schedule_ids = fields.One2many(
        "hr.shift.schedule",
        "shift_request_id",
        string="Shift Schedule",
        help="Shift schedule",
    )
    shift_request_line_ids = fields.One2many(
        "hr.shift.request.line",
        "shift_request_id",
        string="Shift Request Line",
        help="Lines of the shift request",
    )
    # design
    calendar_color = fields.Char(
        "potatos",
        compute="_compute_calendar_color",
        default="#AAAAAA",
    )

    default_day_off = fields.Selection(
        [
            ("saturday", "Saturday"),
            ("sunday", "Sunday"),
            ("monday", "Monday"),
            ("tuesday", "Tuesday"),
            ("wednesday", "Wednesday"),
            ("thursday", "Thursday"),
            ("friday", "Friday"),
        ],
        string="Default Day Off",
        default="saturday",
        help="Default day off for employees in this shift request",
    )

    @api.model
    def create(self, vals_list):
        if vals_list.get("name", _("New")) == _("New"):
            company_id = vals_list.get("company_id", self.env.company.id)
            company = self.env["res.company"].browse(company_id)

            sequence_number = self.env["ir.sequence"].next_by_code(
                "hr.shift.request"
            ) or _("New")

            vals_list["name"] = f"{company.name} Shift Request / {sequence_number}"
        return super(HrShiftRequest, self).create(vals_list)

    def unlink(self):
        self.shift_schedule_ids.unlink()
        return super(HrShiftRequest, self).unlink()

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

    @api.depends("state")
    def _compute_approved(self):
        for request in self:
            request.approved = request.state == "approved"

    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        for request in self:
            if (
                request.start_date
                and request.end_date
                and request.end_date < request.start_date
            ):
                raise ValidationError(_("End Date cannot be earlier than Start Date."))

    @api.onchange("company_id")
    def _onchange_company_id(self):
        self.shift_id = False
        self.department_id = False

    # @api.constrains("employee_ids")
    # def _check_employee_contracts(self):
    #     for request in self:
    #         for employee in request.employee_ids:
    #             if not employee.contract_id:
    #                 raise ValidationError(
    #                     _(
    #                         "Employee %s does not have an active contract please contact HR.",
    #                         employee.name,
    #                     )
    #                 )

    def action_approve(self):
        self.ensure_one()
        if self.request_type == "assign":
            self.approve_assign_request()
        elif self.request_type == "change":
            self.approve_change_request()
        else:
            raise UserError(_("Invalid request type specified."))

    def approve_change_request(self):
        self.ensure_one()
        hr_shift_schedule_obj = self.env["hr.shift.schedule"]
        # for employee in self.employee_ids:
        for line in self.shift_request_line_ids:
            employee = line.employee_id

            # Find the existing shift schedule for the employee within the request's date range
            # change this to lambda
            existing_shift_schedules = hr_shift_schedule_obj.search(
                [
                    ("rel_hr_schedule", "=", employee.contract_id.id),
                    ("start_date", "<=", self.end_date),
                    ("end_date", ">=", self.start_date),
                ],
            )

            if existing_shift_schedules:
                for existing_shift in existing_shift_schedules:
                    potatoes = self._check_overlap(existing_shift)
                    if potatoes:
                        # Case 1: Existing shift is completely within the new shift
                        if (
                            self.start_date <= existing_shift.start_date
                            and self.end_date >= existing_shift.end_date
                        ):
                            existing_shift.sudo().unlink()
                        # Case 2: New shift is completely within the existing shift
                        elif (
                            existing_shift.start_date < self.start_date
                            and existing_shift.end_date > self.end_date
                        ):
                            original_end_date = existing_shift.end_date
                            original_request_id = existing_shift.shift_request_id.id
                            # Split the existing shift into two
                            existing_shift.write(
                                {
                                    "end_date": self.start_date - timedelta(days=1),
                                },
                                True,
                            )

                            hr_shift_schedule_obj.create(
                                {
                                    "start_date": self.end_date + timedelta(days=1),
                                    "end_date": original_end_date,
                                    "rel_hr_schedule": employee.contract_id.id,
                                    "hr_shift": existing_shift.hr_shift.id,
                                    "company_id": self.company_id.id,
                                    "shift_request_id": original_request_id,
                                },
                                True,
                            )
                        elif (
                            self.start_date <= existing_shift.start_date
                            and self.end_date < existing_shift.end_date
                        ):
                            existing_shift.write(
                                {
                                    "start_date": self.end_date + timedelta(days=1),
                                },
                                True,
                            )
                        # Case 4: Existing shift overlaps from the end
                        elif (
                            self.start_date > existing_shift.start_date
                            and self.end_date >= existing_shift.end_date
                        ):
                            existing_shift.write(
                                {"end_date": self.start_date - timedelta(days=1)}, True
                            )

                # Create the new shift schedule after handling overlaps
                hr_shift_schedule_obj.create(
                    {
                        "start_date": self.start_date,
                        "end_date": self.end_date,
                        "rel_hr_schedule": employee.contract_id.id,
                        "hr_shift": self.shift_id.id,
                        "company_id": self.company_id.id,
                        "shift_request_id": self.id,
                        "day_off": line.off_day,
                    },
                    True,
                )
            else:
                raise UserError(
                    _(
                        "No existing shift schedule found for employee %s within the specified date range.",
                        employee.name,
                    )
                )

        self.write({"state": "approved", "approved_by_id": self.env.user.id})

    def approve_assign_request(self):
        # TODO this function should return all emp names that has overlap warnings not only one
        self.ensure_one()
        shift_overlaps = []
        hr_shift_schedual = self.env["hr.shift.schedule"]
        # for employee in self.employee_ids:
        for line in self.shift_request_line_ids:
            employee = line.employee_id
            try:
                hr_shift_schedual.create(
                    {
                        "start_date": self.start_date,
                        "end_date": self.end_date,
                        "rel_hr_schedule": employee.contract_id.id,
                        "hr_shift": self.shift_id.id,
                        "company_id": self.company_id.id,
                        "shift_request_id": self.id,
                        "day_off": line.off_day,
                    }
                )
            except Warning as e:
                if "overlap" in str(e):
                    shift_overlaps.append(str(employee.display_name))
                    continue
                else:
                    raise e

        if shift_overlaps:
            raise UserError(
                _(
                    "The shift times for the selected dates overlap with %s shift times.",
                    ", ".join(shift_overlaps),
                )
            )
        else:
            self.write({"state": "approved", "approved_by_id": self.env.user.id})

    def action_reject(self):
        self.ensure_one()
        self.write({"state": "rejected"})

    def action_submit(self):
        self.ensure_one()
        auto_accept = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("hr_employee_shift.auto_accept")
        )
        if auto_accept:
            self.action_approve()
        else:
            if self.request_type != "change":
                overlap_issues = []
                hr_shift_schedule_obj = self.env["hr.shift.schedule"]
                # for employee in self.employee_ids:
                for line in self.shift_request_line_ids:
                    employee = line.employee_id
                    existing_shift_schedules = hr_shift_schedule_obj.search(
                        [
                            ("rel_hr_schedule", "=", employee.contract_id.id),
                            ("start_date", "<=", self.end_date),
                            ("end_date", ">=", self.start_date),
                        ],
                    )
                    for existing_shift in existing_shift_schedules:
                        if not self._check_overlap(existing_shift.hr_shift):
                            overlap_issues.append(employee.display_name)

                if overlap_issues:
                    raise UserError(
                        _(
                            "The shift times for the selected dates overlap with %s shift times.",
                            ", ".join(overlap_issues),
                        )
                    )
            self.write({"state": "to_approve"})

    def action_reset_to_draft(self):
        self.ensure_one()
        self.shift_schedule_ids.unlink()
        self.write({"state": "draft", "approved_by_id": False})

    @api.onchange("default_day_off")
    def _apply_default_day_off(self):
        for request_line in self.shift_request_line_ids:
            request_line.off_day = self.default_day_off

    # checks if there is overlaps in
    def _check_overlap(self, old_shift):
        new_shift = self.shift_id
        for new_working_period in new_shift.attendance_ids:
            for old_working_period in old_shift.hr_shift.attendance_ids:
                if max(
                    new_working_period.hour_from,
                    old_working_period.hour_from,
                ) < min(new_working_period.hour_to, old_working_period.hour_to):
                    return True
        return False
