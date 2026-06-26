# app/actions/business_actions.py
"""Business Action Handlers.

Each function performs one real business operation (mocked with in-memory data).
LangChain tool wrappers live in app/actions/langchain_tools.py.
"""

from datetime import datetime
from data.sqlite_db import get_employee, insert_ticket, insert_report, list_employees, list_tickets


# ─── Action: Create Ticket ────────────────────────────────────────────────────

def create_ticket(params: dict) -> dict:
    """Create a support/IT ticket and store it in the mock DB."""
    ticket = insert_ticket(
        title=params.get("title", "Untitled Issue"),
        priority=params.get("priority", "medium"),
        description=params.get("description", ""),
    )
    return {
        "success": True,
        "message": f"Ticket {ticket['id']} created successfully.",
        "data": ticket,
    }


# ─── Action: Fetch Employee Info ──────────────────────────────────────────────

def fetch_employee(params: dict) -> dict:
    """Look up employee details by ID."""
    emp_id = params.get("id", "").upper()
    employee = get_employee(emp_id)

    if employee:
        return {"success": True, "message": "Employee found.", "data": employee}
    return {"success": False, "message": f"No employee found with ID or name '{emp_id}'."}


def list_employees_action(params: dict | None = None) -> dict:
    """List employees, optionally filtered by department and/or role."""
    params = params or {}
    department = (params.get("department") or "").strip().lower()
    role = (params.get("role") or "").strip().lower()
    query = (params.get("query") or "").strip().lower()

    employees = list_employees()
    if department:
        employees = [e for e in employees if e["department"].lower() == department]
    if role:
        employees = [e for e in employees if role in e["role"].lower()]
    if query:
        employees = [
            e
            for e in employees
            if query in e["name"].lower()
            or query in e["department"].lower()
            or query in e["role"].lower()
        ]

    return {
        "success": True,
        "message": f"Found {len(employees)} employee(s).",
        "data": employees,
    }


# ─── Action: Generate Report ──────────────────────────────────────────────────

def generate_report(params: dict) -> dict:
    """Generate a summary report based on type and department."""
    report_type = params.get("type", "headcount").lower()
    department = params.get("department", "All")

    employees = list_employees()
    if department != "All":
        employees = [e for e in employees if e["department"].lower() == department.lower()]

    if report_type == "headcount":
        report_data = {
            "total": len(employees),
            "departments": {},
        }
        for emp in employees:
            dept = emp["department"]
            report_data["departments"][dept] = report_data["departments"].get(dept, 0) + 1

    elif report_type == "leave":
        report_data = {
            "employees": [
                {"name": e["name"], "leave_balance": e["leave_balance"]}
                for e in employees
            ]
        }

    elif report_type == "tickets":
        tickets = list_tickets()
        open_tickets = [t for t in tickets if t["status"] == "open"]
        report_data = {
            "total_tickets": len(tickets),
            "open_tickets": len(open_tickets),
            "by_priority": {
                "high": len([t for t in tickets if t["priority"] == "high"]),
                "medium": len([t for t in tickets if t["priority"] == "medium"]),
                "low": len([t for t in tickets if t["priority"] == "low"]),
            },
        }
    else:
        return {"success": False, "message": f"Unknown report type: '{report_type}'"}

    report = insert_report(report_type=report_type, department=department, data=report_data)
    return {"success": True, "message": f"{report_type.title()} report generated.", "data": report}


def search_employees(params: dict) -> dict:
    """Search employees using a free-form query plus optional department/role filters."""
    return list_employees_action(params)


