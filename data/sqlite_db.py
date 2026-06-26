"""SQLite persistence for employees, tickets, and reports."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(os.getenv("AI_ASSISTANT_DB_PATH", Path(__file__).resolve().parent / "assistant.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SEED_EMPLOYEES = [
    {"id": "EMP001", "name": "Ananya Sharma", "department": "Engineering", "role": "Backend Engineer", "leave_balance": 12},
    {"id": "EMP002", "name": "Rahul Mehta", "department": "HR", "role": "HR Manager", "leave_balance": 18},
    {"id": "EMP003", "name": "Priya Nair", "department": "Finance", "role": "Finance Analyst", "leave_balance": 15},
    {"id": "EMP004", "name": "Kabir Singh", "department": "Support", "role": "IT Support Specialist", "leave_balance": 10},
]


def _next_prefixed_id(connection: sqlite3.Connection, table_name: str, prefix: str) -> str:
    row = connection.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
    next_number = int(row["count"]) + 1
    return f"{prefix}-{next_number:04d}"


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    item = dict(row)
    if "data" in item and isinstance(item["data"], str):
        try:
            item["data"] = json.loads(item["data"])
        except json.JSONDecodeError:
            pass
    return item


def init_db() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                role TEXT NOT NULL,
                leave_balance INTEGER NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                priority TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                report_type TEXT NOT NULL,
                department TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        existing = connection.execute("SELECT COUNT(*) AS count FROM employees").fetchone()["count"]
        if existing == 0:
            connection.executemany(
                "INSERT INTO employees (id, name, department, role, leave_balance) VALUES (?, ?, ?, ?, ?)",
                [(emp["id"], emp["name"], emp["department"], emp["role"], emp["leave_balance"]) for emp in SEED_EMPLOYEES],
            )
        connection.commit()


def list_employees() -> list[dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute("SELECT id, name, department, role, leave_balance FROM employees ORDER BY id").fetchall()
        return [dict(row) for row in rows]


def get_employee(identifier: str) -> dict[str, Any] | None:
    if not identifier:
        return None
    term = identifier.strip().lower()
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT id, name, department, role, leave_balance
            FROM employees
            WHERE lower(id) = ? OR lower(name) = ?
            LIMIT 1
            """,
            (term, term),
        ).fetchone()
        if row is None:
            row = connection.execute(
                """
                SELECT id, name, department, role, leave_balance
                FROM employees
                WHERE lower(name) LIKE ?
                ORDER BY id
                LIMIT 1
                """,
                (f"%{term}%",),
            ).fetchone()
        return _row_to_dict(row)


def insert_ticket(title: str, priority: str, description: str) -> dict[str, Any]:
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _connect() as connection:
        ticket_id = _next_prefixed_id(connection, "tickets", "TKT")
        cursor = connection.execute(
            """
            INSERT INTO tickets (id, title, priority, description, status, created_at)
            VALUES (?, ?, ?, ?, 'open', ?)
            """,
            (ticket_id, title, priority, description, created_at),
        )
        connection.commit()
        row = connection.execute(
            "SELECT id, title, priority, description, status, created_at FROM tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()
        return _row_to_dict(row) or {}


def list_tickets() -> list[dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute("SELECT id, title, priority, description, status, created_at FROM tickets ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]


def insert_report(report_type: str, department: str, data: dict[str, Any]) -> dict[str, Any]:
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _connect() as connection:
        report_id = _next_prefixed_id(connection, "reports", "RPT")
        connection.execute(
            """
            INSERT INTO reports (id, report_type, department, data, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (report_id, report_type, department, json.dumps(data, ensure_ascii=False), created_at),
        )
        connection.commit()
        row = connection.execute(
            "SELECT id, report_type, department, data, created_at FROM reports WHERE id = ?",
            (report_id,),
        ).fetchone()
        report = _row_to_dict(row) or {}
        if report:
            report["type"] = report.get("report_type")
        return report


def list_reports() -> list[dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute("SELECT id, report_type, department, data, created_at FROM reports ORDER BY id DESC").fetchall()
        reports: list[dict[str, Any]] = []
        for row in rows:
            report = _row_to_dict(row) or {}
            if report:
                report["type"] = report.get("report_type")
            reports.append(report)
        return reports


def count_tickets() -> int:
    with _connect() as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM tickets").fetchone()
        return int(row["count"])


def count_reports() -> int:
    with _connect() as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM reports").fetchone()
        return int(row["count"])


init_db()
