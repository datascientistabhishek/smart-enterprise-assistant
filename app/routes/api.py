# app/routes/api.py
"""
API Routes
All endpoints live here. Business logic stays in agents/ and actions/.
"""

from fastapi import APIRouter, HTTPException
from app.routes.schemas import AskRequest, AskResponse, ActionResult
from app.agents.assistant_agent import run_agent
from app.core.memory import memory
from data.sqlite_db import count_tickets, count_reports, list_tickets as db_list_tickets, list_reports as db_list_reports, list_employees as db_list_employees

router = APIRouter()


# ─── Main Endpoint ────────────────────────────────────────────────────────────

@router.post("/ask", response_model=AskResponse, summary="Ask the AI assistant a question")
async def ask(request: AskRequest):
    """
    Submit a question to the enterprise AI assistant.
    Supports conversation memory via session_id.
    May trigger a business action (ticket creation, report generation, etc.)
    """
    result = run_agent(question=request.question, session_id=request.session_id)

    action_result = None
    if result.get("action_result"):
        ar = result["action_result"]
        action_result = ActionResult(
            success=ar.get("success", False),
            message=ar.get("message", ""),
            data=ar.get("data"),
        )

    return AskResponse(
        session_id=result["session_id"],
        answer=result["answer"],
        action_result=action_result,
        history_length=result["history_length"],
        error=result.get("error"),
    )


# ─── Read-only Data Endpoints ─────────────────────────────────────────────────

@router.get("/tickets", summary="List all support tickets")
async def list_tickets():
    tickets = db_list_tickets()
    return {"total": len(tickets), "tickets": tickets}


@router.get("/reports", summary="List all generated reports")
async def list_reports():
    reports = db_list_reports()
    return {"total": len(reports), "reports": reports}


@router.get("/employees", summary="List all employees (summary)")
async def list_employees():
    employees = db_list_employees()
    summary = [
        {"id": e["id"], "name": e["name"], "department": e["department"], "role": e["role"]}
        for e in employees
    ]
    return {"total": len(summary), "employees": summary}


# ─── Session Management ───────────────────────────────────────────────────────

@router.delete("/session/{session_id}", summary="Clear conversation history for a session")
async def clear_session(session_id: str):
    memory.clear(session_id)
    return {"message": f"Session '{session_id}' cleared."}


# ─── Health Check ─────────────────────────────────────────────────────────────

@router.get("/health", summary="Health check")
async def health():
    return {
        "status": "ok",
        "active_sessions": memory.session_count(),
        "total_tickets": count_tickets(),
    }
