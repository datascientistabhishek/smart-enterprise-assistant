# app/agents/assistant_agent.py
"""
Assistant Agent
Handles the full reasoning loop:
    1. Build context (system prompt + policy info + conversation history)
    2. Call Groq through LangChain tool calling
    3. Execute tools when the model requests them
    4. Return structured response
"""

import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app.actions.langchain_tools import LANGCHAIN_TOOLS, TOOL_REGISTRY
from app.core.config import groq_llm
from app.core.memory import memory
from app.core.prompts import SYSTEM_PROMPT
from data.mock_db import POLICIES


def _build_system_message() -> str:
    """Inject policy context into the system prompt so the LLM can answer policy Qs."""
    policy_block = "\n\n## Company Policies (use only these for policy questions)\n"
    for topic, text in POLICIES.items():
        policy_block += f"- **{topic.title()}**: {text}\n"
    return SYSTEM_PROMPT + policy_block


def _history_to_messages(history: list[dict]) -> list[HumanMessage | AIMessage | SystemMessage]:
    messages: list[HumanMessage | AIMessage | SystemMessage] = []
    for item in history:
        role = item.get("role")
        content = item.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
        elif role == "system":
            messages.append(SystemMessage(content=content))
    return messages


def _message_content_to_text(content: object) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return " ".join(str(part) for part in content).strip()
    if content is None:
        return ""
    return str(content).strip()


def _execute_tool_call(tool_call: object) -> tuple[str, dict]:
    if isinstance(tool_call, dict):
        tool_name = tool_call.get("name", "")
        tool_args = tool_call.get("args", {})
        tool_call_id = tool_call.get("id", tool_name)
    else:
        tool_name = getattr(tool_call, "name", "")
        tool_args = getattr(tool_call, "args", {})
        tool_call_id = getattr(tool_call, "id", tool_name)

    tool = TOOL_REGISTRY.get(tool_name)
    if not tool:
        return tool_call_id, {
            "success": False,
            "message": f"Unknown tool: {tool_name}",
            "data": None,
        }

    try:
        raw_result = tool.invoke(tool_args)
        if isinstance(raw_result, str):
            try:
                parsed_result = json.loads(raw_result)
            except json.JSONDecodeError:
                parsed_result = {"success": True, "message": raw_result, "data": raw_result}
        elif isinstance(raw_result, dict):
            parsed_result = raw_result
        else:
            parsed_result = {"success": True, "message": str(raw_result), "data": raw_result}
    except Exception as exc:
        parsed_result = {
            "success": False,
            "message": f"Tool execution failed: {exc}",
            "data": None,
        }

    return tool_call_id, parsed_result


def run_agent(question: str, session_id: str) -> dict:
    """
    Core agent loop.
    Returns a dict with: answer, action_result, session_id, history_length.
    """
    history = memory.get_history(session_id)
    memory.add_message(session_id, "user", question)

    conversation = [
        SystemMessage(content=_build_system_message()),
        *_history_to_messages(history),
        HumanMessage(content=question),
    ]

    llm = groq_llm.bind_tools(LANGCHAIN_TOOLS)
    action_result: dict | None = None
    final_answer = ""

    try:
        for _ in range(4):
            response = llm.invoke(conversation)
            conversation.append(response)

            tool_calls = getattr(response, "tool_calls", None) or []
            if not tool_calls:
                final_answer = _message_content_to_text(response.content)
                break

            for tool_call in tool_calls:
                tool_call_id, result = _execute_tool_call(tool_call)
                action_result = result
                conversation.append(
                    ToolMessage(
                        content=json.dumps(result, ensure_ascii=False),
                        tool_call_id=tool_call_id,
                        name=(tool_call.get("name") if isinstance(tool_call, dict) else getattr(tool_call, "name", None)),
                    )
                )

        if not final_answer:
            final_answer = action_result.get("message", "Action completed successfully.") if action_result else ""
    except Exception as e:
        return {
            "session_id": session_id,
            "answer": "I'm having trouble reaching the AI service right now. Please try again.",
            "action_result": None,
            "error": str(e),
            "history_length": len(memory.get_history(session_id)),
        }

    memory.add_message(session_id, "assistant", final_answer or "Action completed successfully.")

    return {
        "session_id": session_id,
        "answer": final_answer if final_answer else "Action completed successfully.",
        "action_result": action_result,
        "error": None,
        "history_length": len(memory.get_history(session_id)),
    }
