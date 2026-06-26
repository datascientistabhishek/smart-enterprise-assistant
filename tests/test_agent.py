"""End-to-end Groq integration tests for the LangChain-based agent."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv


load_dotenv()


MODULES_TO_RESET = [
    "app.core.config",
    "data.sqlite_db",
    "app.actions.business_actions",
    "app.actions.langchain_tools",
    "app.agents.assistant_agent",
    "app.core.memory",
]


pytestmark = pytest.mark.integration


@pytest.fixture()
def live_modules(tmp_path, monkeypatch):
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        pytest.skip("GROQ_API_KEY is required for live Groq integration tests.")

    monkeypatch.setenv("AI_ASSISTANT_DB_PATH", str(tmp_path / "assistant.db"))
    monkeypatch.setenv("GROQ_API_KEY", api_key)

    for module_name in MODULES_TO_RESET:
        sys.modules.pop(module_name, None)

    sqlite_db = importlib.import_module("data.sqlite_db")
    memory_module = importlib.import_module("app.core.memory")
    assistant_agent = importlib.import_module("app.agents.assistant_agent")

    return {
        "sqlite_db": sqlite_db,
        "memory_module": memory_module,
        "assistant_agent": assistant_agent,
    }


@pytest.mark.integration
def test_live_tool_calling_and_ticket_creation(live_modules):
    assistant_agent = live_modules["assistant_agent"]
    memory_module = live_modules["memory_module"]
    sqlite_db = live_modules["sqlite_db"]

    session_id = "groq-live-ticket"
    memory_module.memory.clear(session_id)

    result = assistant_agent.run_agent(
        "Create a support ticket for a laptop that will not boot. Use the create_ticket tool.",
        session_id=session_id,
    )

    assert result["error"] is None
    assert result["action_result"] is not None
    assert result["action_result"]["success"] is True
    assert result["action_result"]["data"]["id"].startswith("TKT-")
    assert sqlite_db.count_tickets() >= 1
    assert result["history_length"] == 2
    assert result["answer"]


@pytest.mark.integration
def test_live_employee_lookup_and_memory(live_modules):
    assistant_agent = live_modules["assistant_agent"]
    memory_module = live_modules["memory_module"]

    session_id = "groq-live-memory"
    memory_module.memory.clear(session_id)

    first = assistant_agent.run_agent(
        "Look up employee EMP001 and tell me who they are. Use the fetch_employee tool.",
        session_id=session_id,
    )
    second = assistant_agent.run_agent(
        "Now tell me whether I can carry forward unused annual leave next year.",
        session_id=session_id,
    )

    assert first["error"] is None
    assert first["action_result"] is not None
    assert first["action_result"]["success"] is True
    assert first["action_result"]["data"]["id"] == "EMP001"
    assert second["error"] is None
    assert second["history_length"] >= 4
    assert second["answer"]


@pytest.mark.integration
def test_live_report_generation(live_modules):
    assistant_agent = live_modules["assistant_agent"]
    memory_module = live_modules["memory_module"]
    sqlite_db = live_modules["sqlite_db"]

    session_id = "groq-live-report"
    memory_module.memory.clear(session_id)

    result = assistant_agent.run_agent(
        "Generate a headcount report for Engineering. Use the generate_report tool.",
        session_id=session_id,
    )

    assert result["error"] is None
    assert result["action_result"] is not None
    assert result["action_result"]["success"] is True
    assert result["action_result"]["data"]["id"].startswith("RPT-")
    assert result["action_result"]["data"]["type"] == "headcount"
    assert sqlite_db.count_reports() >= 1
    assert result["answer"]


@pytest.mark.integration
def test_live_list_all_employees(live_modules):
    assistant_agent = live_modules["assistant_agent"]
    memory_module = live_modules["memory_module"]

    session_id = "groq-live-all-employees"
    memory_module.memory.clear(session_id)

    result = assistant_agent.run_agent(
        "Give me all employees in the company. Use the list_employees tool.",
        session_id=session_id,
    )

    assert result["error"] is None
    assert result["action_result"] is not None
    assert result["action_result"]["success"] is True
    assert isinstance(result["action_result"]["data"], list)
    assert len(result["action_result"]["data"]) >= 3
    assert result["answer"]


@pytest.mark.integration
def test_live_list_hr_employees(live_modules):
    assistant_agent = live_modules["assistant_agent"]
    memory_module = live_modules["memory_module"]

    session_id = "groq-live-hr-employees"
    memory_module.memory.clear(session_id)

    result = assistant_agent.run_agent(
        "Show me employees in HR department. Use the search_employees tool.",
        session_id=session_id,
    )

    assert result["error"] is None
    assert result["action_result"] is not None
    assert result["action_result"]["success"] is True
    employees = result["action_result"]["data"]
    assert isinstance(employees, list)
    assert any(employee["department"] == "HR" for employee in employees)
    assert result["answer"]
