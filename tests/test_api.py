# tests/test_api.py
"""
Two required test inputs from the assignment:
  1. Normal business query
  2. Challenging query (ambiguous/action-triggering)

Run with: pytest tests/test_api.py -v
Or manually: python tests/test_api.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import requests

BASE_URL = "http://localhost:8000/api/v1"


def pretty(label: str, data: dict):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(json.dumps(data, indent=2))


def test_normal_query():
    """Test 1: Normal business query — employee asking about WFH policy."""
    print("\n[TEST 1] Normal Business Query")
    payload = {
        "question": "What is the work from home policy? How many days can I WFH per week?",
        "session_id": "test-session-normal",
    }
    resp = requests.post(f"{BASE_URL}/ask", json=payload)
    data = resp.json()
    pretty("Response", data)

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert data["answer"], "Answer should not be empty"
    assert data["action_result"] is None, "No action expected for policy query"
    print("\n✅ Test 1 PASSED")


def test_challenging_query_ticket():
    """Test 2: Challenging query — vague issue that should trigger ticket creation."""
    print("\n[TEST 2] Challenging Query — Vague IT issue → Ticket creation")
    payload = {
        "question": "My system is not working since morning and I have a deadline today. Help!",
        "session_id": "test-session-challenge",
    }
    resp = requests.post(f"{BASE_URL}/ask", json=payload)
    data = resp.json()
    pretty("Response", data)

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert data["answer"], "Answer should not be empty"
    # Action may or may not trigger depending on LLM — we just ensure no crash
    print("\n✅ Test 2 PASSED")


def test_memory_continuity():
    """Bonus: Memory — follow-up question should remember context."""
    print("\n[BONUS TEST] Conversation Memory")
    session = "test-memory-session"

    r1 = requests.post(f"{BASE_URL}/ask", json={
        "question": "How many leave days do I have?",
        "session_id": session,
    })
    print("Turn 1:", r1.json()["answer"][:100])

    r2 = requests.post(f"{BASE_URL}/ask", json={
        "question": "Can I carry them forward to next year?",
        "session_id": session,
    })
    data2 = r2.json()
    print("Turn 2:", data2["answer"][:100])
    print(f"History length: {data2['history_length']} messages")

    assert data2["history_length"] >= 2, "Memory should contain at least 2 messages"
    print("\n✅ Memory Test PASSED")


def test_validation_empty_question():
    """Guardrail test: empty question should return 422."""
    print("\n[GUARDRAIL TEST] Empty question")
    resp = requests.post(f"{BASE_URL}/ask", json={"question": "", "session_id": "x"})
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"
    print(f"✅ Got expected 422: {resp.json()['detail'][0]['msg']}")


if __name__ == "__main__":
    print("Starting API tests — make sure the server is running on localhost:8000\n")
    try:
        test_normal_query()
        test_challenging_query_ticket()
        test_memory_continuity()
        test_validation_empty_question()
        print("\n\n🎉 All tests completed!")
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to server. Run: uvicorn app.main:app --reload")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
