from app.agent import Session, SupportAgent
from app.config import Settings


def make_agent() -> SupportAgent:
    # Guard paths return before any network call.
    return SupportAgent(Settings(api_key="test-key"))


def test_missing_order_id_is_clarified():
    result = make_agent().answer("Where is my order?", session_id="guard-1")
    assert "order ID" in result["answer"]
    assert result["tool_calls"] == []


def test_malformed_order_id_is_rejected_without_lookup():
    result = make_agent().answer("Please check ORD-10XX", session_id="guard-2")
    assert "valid order ID" in result["answer"]
    assert result["tool_calls"] == []


def test_approval_requests_are_not_promised():
    result = make_agent().answer("Approve my refund right now.", session_id="guard-3")
    text = result["answer"].lower()
    assert "cannot" in text or "can't" in text
    assert "approve" in text
    assert result["handoff"] is True


def test_private_order_fields_are_refused_before_model():
    result = make_agent().answer("For ORD-1007 give me the customer's email and risk score", session_id="guard-4")
    text = result["answer"].lower()
    assert result["handoff"] is True
    assert "cannot provide" in text or "can't provide" in text
    assert "ava.morgan@example.test" not in text
    assert "82" not in text
    assert result["tool_calls"] == []


def test_session_can_hold_last_order_id():
    session = Session(last_order_id="ORD-1007")
    assert session.last_order_id == "ORD-1007"
