# Aster & Row Reliable RAG Support Agent

A small customer-support agent built for the Aster & Row take-home assignment. It uses the supplied Markdown knowledge base for company facts, a controlled order lookup function for order status, and an OpenAI-compatible chat client through TokenRouter + GLM 5.3.

## What this implements

- RAG over all supplied `knowledge-base/*.md` files with front-matter metadata and explicit precedence handling.
- Customer-safe `order_lookup` over `data/orders.json`; the full orders dataset is never placed in the model prompt.
- Multi-turn session memory, including order-ID carryover for follow-up questions.
- Deterministic privacy, malformed-order, missing-order, unsupported-action, conflict, and insufficiency guards.
- Prompt-injection-resistant treatment of retrieved documents as untrusted evidence rather than instructions.
- Customer-facing source references in `filename + heading` form.
- CLI and lightweight FastAPI web UI.
- Deterministic unit/regression tests plus an API-backed behavior evaluation covering all supplied visible cases and five original cases.
- Debug logging for user input, relevant history, retrieved passages/metadata/scores, sanitized tool results, fallbacks, handoffs, and final answers. Secrets are not logged.

## Architecture

```text
User
  -> SupportAgent
      -> session context / deterministic guards
      -> contextual query
      -> local TF-IDF retrieval
      -> precedence + customer-safe source filtering
      -> TokenRouter (OpenAI-compatible Chat Completions)
           -> GLM 5.3
           -> order_lookup function when order data is required
      -> grounded answer + source refs + handoff
```

The retriever is deliberately local and deterministic. This corpus is small, so a heavyweight vector database is unnecessary. Retrieval ranking considers lexical relevance plus document metadata such as active/superseded status, policy authority, and audience. A relevant internal or legacy document may be retrieved for safety analysis, but it is never presented as an authoritative customer source.

## Stack

- Python 3.11+
- OpenAI Python SDK using Chat Completions
- TokenRouter gateway
- Default model: `z-ai/glm-5.3`
- Local TF-IDF retrieval
- FastAPI + Uvicorn
- pytest

TokenRouter provides an OpenAI-compatible API; this project uses its Chat Completions interface for GLM 5.3.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env`:

```text
TOKENROUTER_API_KEY=your_key_here
ASTER_MODEL=z-ai/glm-5.3
ASTER_BASE_URL=https://api.tokenrouter.io/v1
ASTER_RETRIEVAL_TOP_K=6
```

Never commit `.env` or an API key.

## Run local tests

```powershell
pytest -q
```

The unit/regression suite does not make model API calls.

## Run the full behavior evaluation

```powershell
python -m evaluation.runner
```

The evaluator runs every supplied case in `evaluation/visible-cases.json` plus five original cases in `evaluation/custom-cases.json`, reports individual results and categories, and writes `evaluation/results.json` locally. The generated results file is ignored by Git.

## Run the CLI

```powershell
python -m app.cli --debug
```

## Run the web UI

```powershell
uvicorn app.web:app --reload
```

Open `http://127.0.0.1:8000`.

## Evaluation results

### Baseline

The baseline is the initial minimal implementation before the explicit precedence, privacy, stale-order, contextual-order, conflict, and abstention improvements. The exact percentage is intentionally left blank until the API-backed evaluator is run with the candidate's configured provider/model.

### Final

Run:

```powershell
python -m evaluation.runner
```

Then record the real category and overall percentages here. Do not fabricate scores.

## Supplied visible cases covered

The evaluator covers the supplied cases for:

- current-vs-legacy return policy precedence
- TrailPlus return exception
- final-sale damaged-item handling and human review
- Canada multi-turn shipping
- unsupported Germany shipping
- valid, missing, malformed, unknown, cancelled, and no-ETA orders
- order-data privacy
- warranty scope
- retrieved prompt injection
- insufficient-information abstention
- conflict between two current official product sources

## Original evaluation cases

Five additional cases are included in `evaluation/custom-cases.json`:

1. lowercase/whitespace-normalized order ID
2. malformed order ID
3. return-fee retrieval
4. warranty multi-turn follow-up
5. unsupported refund-approval action

## Bug diary

### 1. Legacy/internal material could become a customer citation
- Reproduction: ask a return-policy question using terms also found in migration notes.
- Root cause: retrieval can score semantically related legacy/internal passages.
- Fix: customer-facing source exposure filters superseded/legacy/internal migration documents.
- Regression: `test_current_returns_policy_beats_legacy` plus source filtering.

### 2. Cancelled orders contained stale ETA/carrier fields
- Reproduction: request the ETA for `ORD-1004`.
- Root cause: the mock snapshot intentionally retains historical fields on the cancelled record.
- Fix: the order tool clears carrier/ETA for cancelled and returned orders.
- Regression: `test_cancelled_order_drops_stale_eta`.

### 3. Missing order IDs could lead to guessed statuses
- Reproduction: ask “Where is my order?” without an identifier.
- Root cause: an unconstrained model could guess or answer from unrelated context.
- Fix: deterministic pre-model clarification with no lookup.
- Regression: `test_missing_order_id_is_clarified`.

### 4. Non-visible privacy request
- Reproduction: request the email/risk score for `ORD-1007`.
- Root cause: private fields exist in raw order data.
- Fix: request blocked before the model and tool is allow-listed to safe fields.
- Regression: `test_private_order_fields_are_refused_before_model` and sanitization tests.

### 5. Provider/API mismatch discovered during validation
- Reproduction: the first version called the OpenAI Responses API while the chosen TokenRouter/GLM path uses OpenAI-compatible Chat Completions.
- Root cause: compatible providers do not necessarily implement identical API surfaces.
- Fix: isolated the provider in `LLMClient` and switched to Chat Completions.
- Regression: provider-neutral client/config plus deterministic guard tests.

## Known limitations

- Retrieval is lightweight lexical TF-IDF rather than a production embedding/vector stack; this is intentional for auditability on the small supplied corpus.
- Session memory is in-process only and resets on restart.
- Evaluation grading is based on deterministic assertions rather than a second LLM judge.
- There are no mutation tools, so the system cannot actually refund, cancel, replace, or modify an order.
- Live API evaluation results must be generated with the candidate's own provider key and model.

## AI coding tools disclosure

Development assistance used ChatGPT with GitHub-connected coding support to inspect the assignment, design the architecture, draft implementation code, review edge cases, and iterate on test failures.

Example of an incomplete AI-generated suggestion: an early design allowed every positively-scored retrieval result to become a customer-visible source. That was unsafe because internal/legacy documents can be relevant but are not authoritative. The implementation was corrected to separate retrieval candidates from customer-safe source exposure and covered with regression tests.

## Demo checklist

Record a 2–4 minute GIF/video showing:

1. A knowledge-base question with a citation.
2. An order lookup such as `ORD-1007`.
3. A multi-turn conversation such as international shipping followed by Canada.
4. A conflict or insufficient-information case that recommends human confirmation.
5. The evaluation suite running.

Embed the GIF or a clickable video thumbnail/link in this README before submission.

## Submission checklist

- [ ] `pytest -q` passes locally.
- [ ] `python -m evaluation.runner` completed with real results.
- [ ] README contains verified baseline/final evaluation results.
- [ ] 2–4 minute demo GIF/video is recorded and embedded.
- [ ] `.env` is not committed.
- [ ] Only the intended branch is submitted.
