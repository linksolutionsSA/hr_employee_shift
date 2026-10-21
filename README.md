# Employee Shift (`hr_employee_shift`)

Odoo 18.0 module for scheduling employee shifts and tracking overtime, with an approval workflow
and payroll integration. Based on the Open HRMS Employee Shift addon by Cybrosys Technologies,
customised for the Almosa deployment.

| | |
| --- | --- |
| Version | 18.0.1.0.0 |
| Category | Human Resources |
| License | LGPL-3 |
| Depends on | `base`, `hr`, `resource`, `payroll` |

## Features

- **Shift requests**: draft → to approve → approved / rejected, with chatter and activities.
  A request holds one or more employee lines and a shift type taken from `resource.calendar`.
- **Generate schedule wizard**: assign a shift to many employees or whole departments over a
  date range in one step.
- **Shift schedule ledger** (`hr.shift.schedule`): the timeline of shifts per employee, shown on
  the contract. Overlapping assignments for the same employee are rejected.
- **Default day-off patterns** per assignment (for example Friday).
- **Overtime requests and schedules**: employees request extra hours; approved hours are stored
  in `hr.overtime.schedule` so attendance (e.g. `oh_hr_zk_attendance`) and payroll can use them.
- **Calendar views** for shifts and overtime to see coverage at a glance.
- **Payroll integration**: worked-day lines are computed from the shift schedule
  (`hr.payslip`, `resource.calendar` overrides).
- Arabic translation (`i18n/ar_001.po`).

## Installation

1. Make sure the `payroll` module (Odoo Community payroll) is available in the addons path.
2. Place this folder in your addons path (in this project: `data/addons/`).
3. Install or update it:

```bash
# install
docker exec -it odoo_erp odoo -d link_solutions_2026 -i hr_employee_shift --stop-after-init
# update after code changes, then restart
docker exec -it odoo_erp odoo -d link_solutions_2026 -u hr_employee_shift --stop-after-init
docker compose restart odoo
```

## Configuration

*Settings → Employees* (stored as system parameters under `hr_employee_shift.*`):

| Setting | Parameter | Default | Meaning |
| --- | --- | --- | --- |
| Auto-Accept Shifts | `auto_accept` | off | Accept shifts automatically without approval. |
| Number of Off Days | `number_of_off_days` | 1 | Off days per week. |
| Overtime Rule Code | `overtime_rule_code` | – | Salary rule code used for overtime in payroll. |
| Cutoff Date | `cutoff_date` | 15 | Day of month (1–31) after which shift requests are cut off. |

## Security groups

| Group | Access |
| --- | --- |
| Shifts / User | Sees only their own shifts. |
| Shifts / Manager Department/Company | Sees and submits requests for employees in their department/company. Implies User. |
| Shifts / Administrator | Full access. Implies Manager. |

HR managers and system administrators also have full access through `ir.model.access.csv`.

## Data model

| Model | Purpose |
| --- | --- |
| `hr.shift.request` / `hr.shift.request.line` | Shift change documents and their employee lines. |
| `hr.shift.schedule` | Assigned shifts per employee (ledger). |
| `hr.overtime.request` / `hr.overtime.request.line` | Overtime applications. |
| `hr.overtime.schedule` | Permitted overtime hours. |
| `hr.employee.shift.myschedule` | Employee "my schedule" view. |
| `hr.shift.generate`, `hr.shift.request.add.employees`, `hr.overtime.request.add.employees` | Wizards. |
| `hr.contract`, `hr.employee`, `hr.payslip`, `resource.calendar`, `res.config.settings` | Extended. |

## Module layout

```
models/     business logic and inherited models
wizard/     generate-schedule and add-employees wizards
views/      form, list, calendar and settings views
security/   groups, record rules, access rights
data/       sequences for shift and overtime requests
demo/       demo shift schedules
i18n/       translations
static/     assets and the Apps-store description page
```

## Deployment

`.github/workflows/main.yml` deploys on every push to `main`: it SSHes to the server, pulls the
module and runs `-u hr_employee_shift`. It uses the repository secrets `HOST`, `USERNAME`,
`SSH_PRIVATE_KEY` and `PORT`. The paths in it (`/opt/odoo17/...`) are legacy; check them before
relying on it for this Docker deployment.

## Credits

- Original authors: Cybrosys Techno Solutions / Open HRMS (<https://www.openhrms.com>)
- Contact: <odoo@cybrosys.com>
- Licensed under [LGPL-3](https://www.gnu.org/licenses/lgpl-3.0-standalone.html)
