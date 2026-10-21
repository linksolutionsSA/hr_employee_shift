# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _


class HrShiftSchedule(models.Model):
    _name = "hr.shift.schedule"

    start_date = fields.Date(
        string="Date From", required=True, help="Starting date for the shift"
    )
    end_date = fields.Date(
        string="Date To", required=True, help="Ending date for the shift"
    )
    rel_hr_schedule = fields.Many2one("hr.contract")
    hr_shift = fields.Many2one(
        "resource.calendar", string="Shift", required=True, help="Shift"
    )
    company_id = fields.Many2one("res.company", string="Company", help="Company")
    shift_request_id = fields.Many2one(
        "hr.shift.request", string="Shift Request", ondelete="cascade"
    )
    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        related="rel_hr_schedule.employee_id",
        store=True,
        readonly=True,
    )
    department_id = fields.Many2one(
        "hr.department",
        related="employee_id.department_id",
        string="Department",
        store=True,
    )

    day_off = fields.Selection(
        [
            ("saturday", "Saturday"),
            ("sunday", "Sunday"),
            ("monday", "Monday"),
            ("tuesday", "Tuesday"),
            ("wednesday", "Wednesday"),
            ("thursday", "Thursday"),
            ("friday", "Friday"),
        ],
        string="Day Off",
        default="saturday",
        help="Default day off for employees in this shift schedule",
    )
    # design
    name = fields.Char(
        string="Name",
        required=True,
        compute="_compute_name",
        help="Name of the shift schedule",
    )

    @api.depends("start_date", "end_date")
    def _compute_name(self):
        for record in self:
            record.name = f"{record.employee_id.name} - {record.hr_shift.name}"

    # security related
    @api.onchange("start_date", "end_date")
    def get_department(self):
        """Adding domain to  the hr_shift field"""
        hr_department = None
        if self.start_date:
            hr_department = self.rel_hr_schedule.department_id.id
        return {"domain": {"hr_shift": [("hr_department", "=", hr_department)]}}

    def write(self, vals, no_overlap=False):
        """Overrides the default write method to ensure there are no overlapping
        shift schedules before updating a record.
        This method first checks for any overlapping shift schedules, If no
        overlaps are found, it proceeds to update the record using the parent class's `write` method.
        """
        self._check_overlap(vals, no_overlap)
        return super(HrShiftSchedule, self).write(vals)

    def create(self, vals, no_overlap=False):
        """The create method in the HrShift Schedule class overrides the parent
        class's create function to check for overlapping shift schedules before
         creating a new record."""
        self._check_overlap(vals, no_overlap)
        return super(HrShiftSchedule, self).create(vals)

    def _check_overlap(self, vals, no_overlap=False):
        """The _check_ove rlap method checks for overlapping shift schedules and
        validates that the start date is before the end date. If an overlap is
        detected or the start date is after the end date, it raises a warning."""
        if (
            vals.get("start_date", False)
            and vals.get("end_date", False)
            and not no_overlap
        ):
            shifts = self.env["hr.shift.schedule"].search(
                [("rel_hr_schedule", "=", vals.get("rel_hr_schedule"))]
            )

            for each in shifts:
                if each.start_date <= fields.Date.to_date(
                    vals.get("end_date")
                ) and each.end_date >= fields.Date.to_date(vals.get("start_date")):
                    # TODO if each.hr_shift attendance ids overlaps with the schedual times raise warni
                    for working_period in each.hr_shift.attendance_ids:
                        new_hr_shift = vals.get("hr_shift")
                        if new_hr_shift:
                            new_shift_record = self.env["resource.calendar"].browse(
                                new_hr_shift
                            )
                            for new_working_period in new_shift_record.attendance_ids:
                                # Check for overlap in working hours
                                if max(
                                    working_period.hour_from,
                                    new_working_period.hour_from,
                                ) < min(
                                    working_period.hour_to, new_working_period.hour_to
                                ):
                                    raise Warning(
                                        _(
                                            "The shift times for the selected dates overlap with an existing shift",
                                        )
                                    )
            if vals.get("start_date") > vals.get("end_date"):
                raise Warning(_("Start date should be less than end date."))
        return True
