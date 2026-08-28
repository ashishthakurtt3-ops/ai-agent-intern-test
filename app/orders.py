from __future__ import annotations

from pathlib import Path
import json
import re

ORDER_ID_RE = re.compile(r"^ORD-\d{4}$", re.IGNORECASE)
PUBLIC_FIELDS = {"order_id", "status", "carrier", "estimated_delivery", "customer_safe_message", "shipped_at", "delivered_at"}


class OrderLookup:
    def __init__(self, path: str | Path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.orders = {item["order_id"].upper(): item for item in data["orders"]}

    def lookup(self, order_id: str) -> dict:
        normalized = order_id.strip().upper()
        if not ORDER_ID_RE.fullmatch(normalized):
            return {"ok": False, "error": "invalid_order_id", "message": "That does not look like a valid order ID. Please provide an ID such as ORD-1007."}
        order = self.orders.get(normalized)
        if not order:
            return {"ok": False, "error": "not_found", "message": "Order was not found. Check the order ID or contact support."}

        result = {k: order.get(k) for k in PUBLIC_FIELDS}
        result["order_id"] = normalized
        status = str(order.get("status", "")).lower()
        if status in {"cancelled", "returned"}:
            result["carrier"] = None
            result["estimated_delivery"] = None
            result["tracking_number"] = None
        # Explicitly omit tracking number, customer information, and all internal fields.
        if status == "cancelled":
            result["customer_safe_message"] = "The order was cancelled and will not be shipped."
        return {"ok": True, "order": result}
