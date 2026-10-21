# Open HRMS Employee Shift (`hr_employee_shift`)

## Overview
The **Open HRMS Employee Shift** module provides a robust framework for managing complex employee work patterns. It extends Odoo's standard resource and contract management to allow for dynamic shift scheduling, shift rotation requests, and overtime tracking. This module is essential for organizations with multiple work timings, night shifts, or flexible labor requirements.

## Key Features
*   **Shift Request Workflow**: Employees or managers can submit shift requests. These follow a formal approval process (Draft → To Approve → Approved/Rejected).
*   **Batch Shift Generation**: Includes a powerful "Generate Schedule" wizard to assign specific shifts to multiple employees or entire departments over a defined date range.
*   **Dynamic Schedules**: Allows multiple work schedules per contract. Unlike standard Odoo (which usually assumes one fixed calendar), this module tracks a timeline of shifts via the **Shift Schedule** model.
*   **Overtime Management**: 
    *   Formal **Overtime Requests** linked to specific dates and hours.
    *   **Overtime Schedules** that define exactly when an employee is permitted to work extra hours.
*   **Visual Scheduling**: Integrated **Calendar Views** for both Shifts and Overtime, allowing managers to see coverage at a glance.
*   **Department-Specific Rotations**: Support for assigning default "Day Off" patterns (e.g., Friday, Sunday) within specific shift assignments.
*   **Conflict Validation**: Automatic checks to ensure shift assignments do not overlap for the same employee.

## Workflows
### 1. Shift Management
*   **Request**: Define the shift type (from Odoo's `resource.calendar`) and the duration.
*   **Lines**: Add multiple employees to a single request.
*   **Execution**: Once approved, the system populates the `hr.shift.schedule` which is visible on the Employee's Contract.

### 2. Overtime Management
*   **Request**: Employees apply for extra hours.
*   **Allocation**: Approved overtime is recorded in the `hr.overtime.schedule`, which is then used by modules like `oh_hr_zk_attendance` to validate extra attendance time.

## Technical Details
*   **Odoo Version**: 18.0
*   **Core Models**:
    *   `hr.shift.request`: Primary document for shift change applications.
    *   `hr.shift.schedule`: The ledger of all assigned shifts per employee.
    *   `hr.overtime.request`: Primary document for extra hour applications.
    *   `hr.overtime.schedule`: The ledger of permitted extra hours.
    *   `hr.contract` (Inherited): Houses the Shift and Overtime schedule tabs.
*   **Dependencies**: 
    *   `hr`: Base employee management.
    *   `resource`: Base calendar/working time logic.
    *   `payroll`: Integration for worked days and overtime payment calculations.

## Use Case
This module is ideal for hospitals, retail stores, manufacturing plants, and security firms where employees rotate between morning, evening, and night duties, and where precise tracking of extra hours is critical for payroll accuracy.
