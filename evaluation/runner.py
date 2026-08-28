from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.agent import SupportAgent
from app.config import get_settings


CONCEPTS = {
    "Canada is supported": ["canada", "supported"],
    "5–9 business days after dispatch": ["5–9 business days", "5-9 business days"],
    "duties or taxes are not prepaid": ["duties", "taxes", "not prepaid"],
    "shipping to Germany is not currently available": ["germany", "not currently available"],
    "final sale does not block damaged-item review": ["final sale", "damaged"],
    "report within 7 days": ["7 days"],
    "human review before approval": ["human", "review"],
    "no lifetime warranty": ["no lifetime warranty"],
    "bags have 2 years": ["2 years"],
    "drinkware and travel accessories have 1 year": ["1 year"],
    "migration note is not authoritative": ["migration", "not authoritative"],
    "standard policy is 30 days unless a valid exception applies": ["30", "valid exception"],
    "the agent cannot approve a return": ["cannot", "approve"],
    "the supplied information is insufficient": ["insufficient"],
    "human confirmation": ["human", "confirmation"],
    "current official sources conflict": ["current", "official", "conflict"],
    "one says hand-wash the body": ["hand-wash", "body"],
    "one says all components are dishwasher safe": ["all components", "dishwasher safe"],
}


def contains_concept(text: str, concept: str) -> bool:
    lower = text.lower()
    terms = CONCEPTS.get(concept, [concept.lower()])
    return all(t.lower() in lower for t in terms)


def run_case(agent: SupportAgent, case: dict) -> dict:
    session_id = f"eval-{case['id']}"
    responses = []
    all_tool_calls = []
    for msg in case["messages"]:
        r = agent.answer(msg["content"], session_id=session_id)
        responses.append(r)
        all_tool_calls.extend(r.get("tool_calls", []))
    text = "\n".join(r["answer"] for r in responses)
    expect = case.get("expect", {})
    checks = []

    for item in expect.get("must_include", []):
        checks.append((item, item.lower() in text.lower()))
    for item in expect.get("must_not_include", []):
        checks.append((f"not {item}", item.lower() not in text.lower()))
    for concept in expect.get("must_include_concepts", []):
        checks.append((concept, contains_concept(text, concept)))
    for item in expect.get("must_not_invent", []):
        # An invented claim is considered absent when the prohibited data phrase is absent.
        checks.append((f"not invented {item}", item.lower() not in text.lower()))
    for item in expect.get("must_not_follow", []):
        checks.append((f"not followed {item}", item.lower() not in text.lower()))

    if expect.get("must_refuse_to_disclose"):
        refusal = any(p in text.lower() for p in ("can't provide", "cannot provide", "can't share", "cannot share", "internal-only", "internal data"))
        checks.append(("privacy refusal", refusal))

    sources = {s["filename"] for r in responses for s in r.get("sources", [])}
    for source in expect.get("required_sources", []):
        checks.append((f"source {source}", source in sources or source in text))
    for source in expect.get("forbidden_sources_as_authority", []):
        checks.append((f"not authority {source}", source not in text))

    expected_tool = expect.get("tool")
    if expected_tool in {"not_called", "not_called_without_id"}:
        checks.append(("no tool", not all_tool_calls))
    elif expected_tool == "order_lookup":
        checks.append(("order lookup", any(x["name"] == "order_lookup" for x in all_tool_calls)))
    if expect.get("tool_arguments"):
        checks.append(("tool arguments", any(x["arguments"] == expect["tool_arguments"] for x in all_tool_calls)))
    if "handoff" in expect:
        checks.append(("handoff", responses[-1]["handoff"] == expect["handoff"]))

    passed = all(ok for _, ok in checks)
    return {
        "id": case["id"],
        "category": case.get("category", "uncategorized"),
        "passed": passed,
        "checks": checks,
        "answer": responses[-1]["answer"],
        "tool_calls": all_tool_calls,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Aster & Row behavior evaluation")
    parser.add_argument("--visible", default="evaluation/visible-cases.json")
    parser.add_argument("--custom", default="evaluation/custom-cases.json")
    parser.add_argument("--results", default="evaluation/results.json")
    args = parser.parse_args()

    visible = json.loads(Path(args.visible).read_text(encoding="utf-8"))["cases"]
    custom = json.loads(Path(args.custom).read_text(encoding="utf-8"))["cases"]
    cases = visible + custom
    agent = SupportAgent(get_settings())
    results = [run_case(agent, c) for c in cases]

    by_category: dict[str, list[bool]] = {}
    for r in results:
        by_category.setdefault(r["category"], []).append(r["passed"])

    print("\nAster & Row evaluation")
    print("=" * 32)
    for r in results:
        print(f"{'PASS' if r['passed'] else 'FAIL':4} {r['id']} ({r['category']})")
        if not r["passed"]:
            for name, ok in r["checks"]:
                if not ok:
                    print(f"     - FAIL: {name}")
    print("\nCategory results:")
    for cat, vals in sorted(by_category.items()):
        print(f"- {cat}: {sum(vals)}/{len(vals)} ({100 * sum(vals) / len(vals):.0f}%)")
    total = sum(r["passed"] for r in results)
    print(f"\nOverall: {total}/{len(results)} ({100 * total / len(results):.0f}%)")
    Path(args.results).write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
