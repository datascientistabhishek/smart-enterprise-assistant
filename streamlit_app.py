"""Simple Streamlit UI for the AI Enterprise Assistant."""

from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st


DEFAULT_BASE_URL = os.getenv("ASSISTANT_API_BASE_URL", "http://127.0.0.1:8000/api/v1")


st.set_page_config(
    page_title="AI Enterprise Assistant",
    page_icon="AI",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
        .hero {
            background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 55%, #38bdf8 100%);
            color: white;
            border-radius: 20px;
            padding: 1.5rem 1.75rem;
            box-shadow: 0 18px 48px rgba(15, 23, 42, 0.18);
            margin-bottom: 1rem;
        }
        .hero h1 { margin: 0; font-size: 2rem; }
        .hero p { margin: 0.35rem 0 0; opacity: 0.92; }
        .metric-card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 1rem;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
        }
        .small-label {
            font-size: 0.8rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.35rem;
        }
        .value {
            font-size: 1.4rem;
            font-weight: 700;
            color: #0f172a;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def api_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def safe_get(url: str) -> tuple[Any, str | None]:
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json(), None
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


def send_question(base_url: str, question: str, session_id: str) -> dict:
    response = requests.post(
        api_url(base_url, "/ask"),
        json={"question": question, "session_id": session_id},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def init_state() -> None:
    st.session_state.setdefault("session_id", "streamlit-session")
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("base_url", DEFAULT_BASE_URL)
    st.session_state.setdefault("last_response", None)


def add_message(role: str, content: str) -> None:
    st.session_state.messages.append({"role": role, "content": content})


def render_metric(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="small-label">{label}</div>
            <div class="value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


init_state()


with st.sidebar:
    st.subheader("Connection")
    st.session_state.base_url = st.text_input("API base URL", value=st.session_state.base_url)
    st.session_state.session_id = st.text_input("Session ID", value=st.session_state.session_id)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
    with col_b:
        if st.button("Reset session", use_container_width=True):
            st.session_state.session_id = "streamlit-session"
            st.session_state.messages = []

    st.divider()

    health_data, health_error = safe_get(api_url(st.session_state.base_url, "/health"))
    st.subheader("Backend Status")
    if health_error:
        st.error(f"Backend not reachable: {health_error}")
    else:
        st.success("Backend online")
        st.write(f"Active sessions: {health_data.get('active_sessions', 0)}")
        st.write(f"Tickets stored: {health_data.get('total_tickets', 0)}")

    st.divider()
    st.caption("Quick links")
    st.link_button("Open API docs", st.session_state.base_url.replace("/api/v1", "/docs"))


st.markdown(
    """
    <div class="hero">
        <h1>AI Enterprise Assistant</h1>
        <p>Chat with the Groq-powered assistant, create tickets, and inspect stored data from one simple UI.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


health_col, tickets_col, reports_col = st.columns(3)
with health_col:
    render_metric("Session ID", st.session_state.session_id)
with tickets_col:
    ticket_data, _ = safe_get(api_url(st.session_state.base_url, "/tickets"))
    render_metric("Tickets", str(ticket_data.get("total", 0)) if isinstance(ticket_data, dict) else "-")
with reports_col:
    report_data, _ = safe_get(api_url(st.session_state.base_url, "/reports"))
    render_metric("Reports", str(report_data.get("total", 0)) if isinstance(report_data, dict) else "-")


chat_tab, data_tab = st.tabs(["Chat", "Data Explorer"])

with chat_tab:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    prompt = st.chat_input("Ask the enterprise assistant anything...")

    if prompt:
        add_message("user", prompt)
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = send_question(st.session_state.base_url, prompt, st.session_state.session_id)
                    st.session_state.last_response = result
                    answer = result.get("answer", "")
                    add_message("assistant", answer)
                    st.write(answer)

                    action_result = result.get("action_result")
                    if action_result:
                        st.success(action_result.get("message", "Action completed."))
                        with st.expander("Action details", expanded=False):
                            st.json(action_result)
                except requests.HTTPError as exc:
                    st.error(f"Backend returned an error: {exc.response.text if exc.response is not None else exc}")
                except requests.RequestException as exc:
                    st.error(f"Could not reach the backend: {exc}")


with data_tab:
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Employees")
        employees_data, employees_error = safe_get(api_url(st.session_state.base_url, "/employees"))
        if employees_error:
            st.error(employees_error)
        else:
            st.dataframe(employees_data.get("employees", []), use_container_width=True, hide_index=True)

    with right_col:
        st.subheader("Tickets")
        tickets_data, tickets_error = safe_get(api_url(st.session_state.base_url, "/tickets"))
        if tickets_error:
            st.error(tickets_error)
        else:
            st.dataframe(tickets_data.get("tickets", []), use_container_width=True, hide_index=True)

    st.subheader("Reports")
    reports_data, reports_error = safe_get(api_url(st.session_state.base_url, "/reports"))
    if reports_error:
        st.error(reports_error)
    else:
        st.dataframe(reports_data.get("reports", []), use_container_width=True, hide_index=True)
