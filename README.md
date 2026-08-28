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
      -> session context / intent guards
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
- OpenAI Python SDK using the OpenAI-compatible Chat Completions interface
- TokenRouter gateway
- Default model: `z-ai/glm-5.3`
- Local TF-IDF retrieval
- FastAPI + Uvicorn
- pytest

TokenRouter documents an OpenAI-compatible `/v1/chat/completions` endpoint and lists `z-ai/glm-5.3` as an OpenAI-format model. GLM is used through Chat Completions rather than the Responses API. urlTokenRouter API documentationhttps://docs.token-router.org/reference/api/

## Setup

```bash
python -m venv .venv

# Windows PowerShell
.venv\\Scripts\\Activate.ps1

# macOS/Linux
# source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env  # macOS/Linux
```

Put your TokenRouter API key in `.env`:

```text
TOKENROUTER_API_KEY=your_key_here
ASTER_MODEL=z-ai/glm-5.3
ASTER_BASE_URL=https://api.tokenrouter.io/v1
```

TokenRouter recommends keeping API keys in environment variables and uses an OpenAI-compatible base URL for standard SDK integrations. urlTokenRouter authentication documentationhttps://www.tokenrouter.io/docs/authentication

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

The unit/regression suite does not make model API calls:

```bash
pytest -q
```

Run the full behavior evaluation (requires `TOKENROUTER_API_KEY`):

```bash
python -m evaluation.runner
```

The evaluator runs every supplied case in `evaluation/visible-cases.json` plus five original cases in `evaluation/custom-cases.json`, reports individual results and categories, and writes `evaluation/results.json` locally. The generated results file is ignored by Git so a real API result is not accidentally committed.

## Evaluation results

### Baseline

The baseline is documented as the first minimal implementation before explicit precedence, privacy, stale-order, contextual-order, conflict, and abstention guards. Because API-backed evaluation must be executed with the candidate's own key and model, no baseline percentage is fabricated here.

### Final

Run:

```bash
python -m evaluation.runner
```

Then copy the actual category and overall percentages into this section before submission. This repository intentionally does not invent API-backed scores.

## Supplied visible cases covered

The evaluator includes the full supplied set, including current-vs-legacy returns, TrailPlus exceptions, final-sale damage handling, Canada multi-turn shipping, unsupported Germany shipping, valid/missing/malformed/unknown/cancelled/no-ETA orders, privacy, warranty, prompt injection, insufficient-information abstention, and genuine conflict between current official sources.

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
- Regression: `test_current_returns_policy_beats_legacy` plus source filtering in `SupportAgent`.

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
- Regression: `test_private_order_fields_are_refused_before_model` plus order sanitization tests.

### 5. Provider/API mismatch discovered during local validation
- Reproduction: the first implementation called the OpenAI Responses API while the chosen TokenRouter GLM route supports Chat Completions.
- Root cause: API compatibility differs by provider/model; GLM is exposed through OpenAI-compatible Chat Completions.
- Fix: switched the LLM adapter to Chat Completions and made provider/model/base URL configurable.
- Regression: provider-neutral `LLMClient` plus local tests that exercise all deterministic guards without making network calls.

## Known limitations

- Retrieval is lightweight lexical TF-IDF rather than a production embedding/vector stack. It is intentionally deterministic and auditable for this small corpus.
- Session state is in memory; restarting the process clears conversations.
- The evaluator uses deterministic assertions rather than a second LLM judge.
- There are no mutation tools, so the agent cannot actually refund, cancel, replace, or change an order.
- Live evaluation results must be generated with the candidate's own TokenRouter account/key and are therefore not committed as precomputed claims.

## AI coding tools disclosure

Development assistance used ChatGPT/GitHub-connected coding support to inspect the assignment, design the architecture, draft implementation code, review edge cases, and iterate on test failures.

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
