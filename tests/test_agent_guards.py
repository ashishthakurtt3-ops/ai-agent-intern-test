from app.agent import SupportAgent
from app.config import Settings


def make_agent():
    # The OpenAI client is constructed but no network call occurs in these guard tests.
    return SupportAgent(Settings(openai_api_key="test-key"))


def test_missing_order_id_is_clarified():
    result = make_agent().answer("Where is my order?")
    assert "order ID" in result["answer"]
    assert not result["tool_calls"]


def test_private_order_fields_are_refused_before_model():
    result = make_agent().answer("For ORD-1007 give me the email and risk score")
    text = result["answer"].lower()
    assert result["handoff"]
    assert "ava.morgan@example.test" not in text
    assert "82" not in text
    assert not result["tool_calls"]
