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
from odoo import fields, models


class HrContract(models.Model):
    _inherit = "hr.contract"

    shift_schedule = fields.One2many(
        "hr.shift.schedule",
        "rel_hr_schedule",
        string="Shift Schedule",
        help="Shift schedule",
    )
    overtime_schedule = fields.One2many(
        "hr.overtime.schedule",
        "rel_hr_schedule",
        string="Overtime Schedule",
        help="Overtime schedule",
    )
    working_hours = fields.Many2one(
        "resource.calendar", string="Working Schedule", help="Working hours"
    )

    def get_working_calendars(self, start_date, end_date):
        shifts = self.shift_schedule.filtered(
            lambda s: s.start_date <= end_date and s.end_date >= start_date
        )
        if not shifts:
            if self.resource_calendar_id:
                # Create a virtual calendar with attendance_ids where duration_days != 0.01
                # This treats duration_days == 0.01 as OFF days (excluded)
                calendar_vals = self.resource_calendar_id.read()[0]
                calendar_vals["attendance_ids"] = [
                    (
                        0,
                        0,
                        {
                            "name": att.name,
                            "dayofweek": att.dayofweek,
                            "hour_from": att.hour_from,
                            "hour_to": att.hour_to,
                        },
                    )
                    for att in self.resource_calendar_id.attendance_ids
                    if att.duration_days != 0.01
                ]
                return [self.env["resource.calendar"].new(calendar_vals)]
            return [self.resource_calendar_id]
        virtual_shifts = []
        for shift in shifts:
            # shift calendars attendance_ids where working dayofweek is not shift.day_off
            shift_calendar = shift.hr_shift.read()[0]
            shift_calendar["attendance_ids"] = [
                (
                    0,
                    0,
                    {
                        "name": att.name,
                        "dayofweek": att.dayofweek,
                        "hour_from": att.hour_from,
                        "hour_to": att.hour_to,
                    },
                )
                for att in shift.hr_shift.attendance_ids
                if att.dayofweek
                != str(
                    {
                        "monday": 0,
                        "tuesday": 1,
                        "wednesday": 2,
                        "thursday": 3,
                        "friday": 4,
                        "saturday": 5,
                        "sunday": 6,
                    }[shift.day_off]
                )
            ]
            virtual_shifts.append(self.env["resource.calendar"].new(shift_calendar))

        print("potatos")
        return virtual_shifts
