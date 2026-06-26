"""LangChain tool wrappers for enterprise actions."""

import json

from langchain_core.tools import tool

from app.actions.business_actions import create_ticket as create_ticket_action
from app.actions.business_actions import fetch_employee as fetch_employee_action
from app.actions.business_actions import generate_report as generate_report_action
from app.actions.business_actions import list_employees_action as list_employees_action
from app.actions.business_actions import search_employees as search_employees_action


def _to_json(result: dict) -> str:
    return json.dumps(result, ensure_ascii=False)


@tool("create_ticket")
def create_ticket_tool(title: str, priority: str = "medium", description: str = "") -> str:
    """Create a support or IT ticket in the mock database."""
    return _to_json(create_ticket_action({"title": title, "priority": priority, "description": description}))


@tool("fetch_employee")
def fetch_employee_tool(identifier: str) -> str:
    """Fetch employee information by employee ID or name."""
    return _to_json(fetch_employee_action({"id": identifier}))


@tool("generate_report")
def generate_report_tool(report_type: str = "headcount", department: str = "All") -> str:
    """Generate a company report."""
    return _to_json(generate_report_action({"type": report_type, "department": department}))


@tool("list_employees")
def list_employees_tool(department: str = "", role: str = "") -> str:
    """List all employees, optionally filtered by department or role."""
    return _to_json(list_employees_action({"department": department, "role": role}))


@tool("search_employees")
def search_employees_tool(query: str = "", department: str = "", role: str = "") -> str:
    """Search employees using free-form text and optional department or role filters."""
    return _to_json(search_employees_action({"query": query, "department": department, "role": role}))


LANGCHAIN_TOOLS = [
    create_ticket_tool,
    fetch_employee_tool,
    generate_report_tool,
    list_employees_tool,
    search_employees_tool,
]

TOOL_REGISTRY = {
    "create_ticket": create_ticket_tool,
    "fetch_employee": fetch_employee_tool,
    "generate_report": generate_report_tool,
    "list_employees": list_employees_tool,
    "search_employees": search_employees_tool,
}