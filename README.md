# Aster & Row Reliable RAG Support Agent

A small customer-support agent built for the Aster & Row take-home assignment. It uses the supplied Markdown knowledge base for company facts, a controlled order lookup function for order status, and OpenAI for grounded response generation.

## What this implements

- RAG over `knowledge-base/` with front-matter metadata and document precedence.
- Customer-safe `order_lookup` over `data/orders.json` without passing the complete orders file to the model.
- Multi-turn session memory for contextual follow-ups.
- Deterministic privacy and missing-order guards.
- Prompt-injection-resistant handling of retrieved content as untrusted data.
- Source references for knowledge-backed responses.
- CLI and a lightweight FastAPI web UI.
- Deterministic unit/regression tests plus behavior-level evaluation covering all supplied visible cases and five original cases.
- Debug logging of retrieval, tool calls, fallbacks, and responses without logging secrets.

## Architecture

```text
User
  -> SupportAgent
      -> contextual query + TF-IDF retrieval
      -> precedence-aware source ranking
      -> OpenAI Responses API
           -> order_lookup function when an order ID is needed
      -> grounded customer response + source refs + handoff
```

The retriever is intentionally local and deterministic. Active official/customer-facing documents receive higher precedence; superseded/legacy/internal migration material is treated as untrusted or non-authoritative and is not exposed as a customer citation.

## Stack

- Python 3.12+
- OpenAI Responses API
- Default model: `gpt-5.6-luna`
- Local TF-IDF lexical retrieval (no vector database required)
- FastAPI + Uvicorn
- pytest

## Setup

```bash
python -m venv .venv
# Windows PowerShell
.venv\\Scripts\\Activate.ps1
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env  # macOS/Linux
```

Put your API key in `.env`:

```text
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5.6-luna
```

Never commit `.env` or an API key.

## Run the CLI

```bash
python -m app.cli --debug
```

## Run the web UI

```bash
uvicorn app.web:app --reload
```

Open `http://127.0.0.1:8000`.

## Run tests

Unit/regression tests do not require an OpenAI API call:

```bash
pytest -q
```

Run the full behavior evaluation (requires `OPENAI_API_KEY`):

```bash
python -m evaluation.runner
```

The runner executes every supplied case in `evaluation/visible-cases.json` plus the five original cases in `evaluation/custom-cases.json`, prints per-case/category results, and writes a local `evaluation/results.json`.

## Evaluation results

### Baseline

Initial baseline was the first minimal implementation before precedence/source filtering and deterministic safety guards. Record the first local `python -m evaluation.runner` output here.

### Final

Record the verified local `python -m evaluation.runner` output here, including per-category and overall scores. This repository does not fabricate API-backed test results when they have not been executed.

## Bug diary

### 1. Legacy/internal material could become a customer citation
- Reproduction: ask a return-policy question using terms also found in migration notes.
- Root cause: retrieval can score semantically related legacy/internal passages.
- Fix: customer-facing source exposure filters superseded/legacy/internal migration documents.
- Regression: `test_current_returns_policy_beats_legacy` and source filtering in `SupportAgent`.

### 2. Cancelled orders contained stale ETA/carrier fields
- Reproduction: request the ETA for `ORD-1004`.
- Root cause: the snapshot intentionally retains historical ETA/carrier values on the cancelled record.
- Fix: the order tool clears stale carrier/ETA data for cancelled and returned orders and uses the safe status message.
- Regression: `test_cancelled_order_drops_stale_eta`.

### 3. Missing order IDs could lead to guessed statuses
- Reproduction: ask “Where is my order?” with no identifier.
- Root cause: an unconstrained model could answer generically or infer an order.
- Fix: deterministic pre-model guard asks for the order ID and performs no lookup.
- Regression: `test_missing_order_id_is_clarified`.

### 4. Additional non-visible security case
- Reproduction: request the email/risk score for `ORD-1007`.
- Root cause: private fields exist in the raw order object.
- Fix: private-data request is rejected before the model is called and the lookup tool itself is allow-listed.
- Regression: `test_private_order_fields_are_refused_before_model` and order sanitization tests.

## Known limitations

- Retrieval is lightweight lexical TF-IDF rather than a production embedding/vector stack. It is intentionally deterministic and easy to audit for this small corpus.
- Session state is in memory; restarting the process clears conversations.
- The evaluator uses deterministic assertions rather than a second LLM judge.
- There are no mutation tools, so the agent cannot actually refund, cancel, replace, or change an order.

## AI coding tools disclosure

Development assistance used ChatGPT/GitHub-connected coding support to inspect the assignment, design the architecture, draft implementation code, and review edge cases. All generated code must be locally executed and reviewed before submission.

Example of an incomplete AI-generated suggestion: an early design allowed every positively-scored retrieval result to become a customer-visible source. That was unsafe because internal/legacy documents can be relevant but are not authoritative. The implementation was corrected to separate retrieval candidates from customer-safe source exposure and covered with regression tests.

## Demo checklist

Record a 2–4 minute GIF/video showing:

1. A policy question with a source citation.
2. An order lookup such as `ORD-1007`.
3. A multi-turn question such as international shipping followed by Canada.
4. A conflict/insufficient-information case that recommends human confirmation.
5. The evaluation suite running.

Embed the GIF or a clickable video thumbnail in this README before submission.

## Original assignment

The supplied assignment asks for a reliable RAG support agent, safe order lookup, multi-turn context, prompt/content safety, a behavior-level evaluation suite, observability, and a minimal interface. See the original repository history for the unmodified assignment README.
