from app.orders import OrderLookup


def test_valid_lookup_is_sanitized(tmp_path):
    tool = OrderLookup("data/orders.json")
    result = tool.lookup(" ord-1007 ")
    assert result["ok"]
    order = result["order"]
    assert order["status"] == "shipped"
    assert order["carrier"] == "UPS"
    assert "email" not in order
    assert "shipping_address" not in order
    assert "internal" not in order
    assert "risk_score" not in order


def test_cancelled_order_drops_stale_eta():
    order = OrderLookup("data/orders.json").lookup("ORD-1004")["order"]
    assert order["status"] == "cancelled"
    assert order["estimated_delivery"] is None
    assert order["carrier"] is None


def test_unknown_and_malformed_ids():
    tool = OrderLookup("data/orders.json")
    assert tool.lookup("ORD-9999")["error"] == "not_found"
    assert tool.lookup("ORD-10XX")["error"] == "invalid_order_id"
