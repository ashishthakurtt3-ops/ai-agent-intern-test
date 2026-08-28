# Aster & Row Reliable RAG Support Agent

A small customer-support agent built for the Aster & Row take-home assignment. It uses the supplied Markdown knowledge base for company facts, a controlled order lookup function for order status, and OpenAI for grounded response generation.

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
- Optional GitHub Actions execution of the full API-backed evaluation when the repository has an `OPENAI_API_KEY` secret.

## Architecture

```text
User
  -> SupportAgent
      -> session context / intent guards
      -> contextual query
      -> local TF-IDF retrieval
      -> precedence + customer-safe source filtering
      -> OpenAI Responses API
           -> order_lookup function when an order ID is required
      -> grounded answer + source refs + handoff flag
```

The retriever is deliberately local and deterministic. This corpus is small, so a heavyweight vector database is unnecessary. Retrieval ranking considers lexical relevance plus document metadata such as active/superseded status, policy authority, and audience. A relevant internal or legacy document may be retrieved for safety analysis, but it is never presented as an authoritative customer source.

## Stack

- Python 3.12+
- OpenAI Responses API
- Default model: `gpt-5.6-luna` (cost-sensitive OpenAI model)
- Local TF-IDF retrieval
- FastAPI + Uvicorn
- pytest

The selected model is an OpenAI API model available through the Responses API and designed for cost-sensitive workloads. urlOpenAI model documentationhttps://platform.openai.com/docs/models/gpt-4-turbo-and-gpt-4

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

Examples:

```text
Where can I return an unused backpack?
Where is ORD-1007?
When will it arrive?
Do you ship internationally?
What about Canada, and how long does it take?
```

## Run the web UI

```bash
uvicorn app.web:app --reload
```

Open `http://127.0.0.1:8000`.

The web UI preserves a browser session ID so follow-up questions remain in the same conversation.

## Run tests

The unit/regression suite does not make OpenAI API calls:

```bash
pytest -q
```

Run the full behavior evaluation (requires `OPENAI_API_KEY`):

```bash
python -m evaluation.runner
```

The evaluator runs every supplied case in `evaluation/visible-cases.json` plus five original cases in `evaluation/custom-cases.json`, reports individual results and categories, and writes `evaluation/results.json` locally. The generated results file is ignored by Git so a real API result is not accidentally committed.

## Evaluation results

### Baseline

A baseline was established conceptually from the initial minimal implementation: it lacked reliable source filtering, explicit stale-order protection, contextual order carryover, malformed-order handling, and deterministic privacy/action guards. Because the API-backed evaluator has not been executed in this development environment, no baseline percentage is fabricated here.

### Final

Run:

```bash
python -m evaluation.runner
```

Then copy the actual category and overall percentages into this section before submission. This repository intentionally does not invent API-backed scores.

## Supplied visible cases covered

The evaluator includes the full supplied set, including:

- current vs legacy return-window precedence
- TrailPlus return exception
- final-sale damaged-item exception and human review
- Canada multi-turn shipping
- unsupported Germany shipping
- valid, missing, malformed, unknown, cancelled, and no-ETA orders
- order-data privacy
- warranty scope
- retrieved prompt injection
- insufficient-information abstention
- genuine conflict between two current official product sources

## Original evaluation cases

Five additional cases are included in `evaluation/custom-cases.json`:

1. lowercase/whitespace-normalized order ID
2. malformed order ID
3. standard return-fee lookup
4. warranty multi-turn follow-up
5. unsupported refund approval action

## Bug diary

### 1. Legacy/internal material could become a customer citation
- **Reproduce:** Ask a return-policy question with wording that also matches migration content.
- **Root cause:** Retrieval relevance and customer citation authority are different concerns.
- **Fix:** Separate retrieval candidates from customer-visible sources; superseded/legacy/internal sources can be evidence for analysis but are filtered from authority citations.
- **Regression:** `test_current_returns_policy_beats_legacy` plus source filtering in `SupportAgent`.

### 2. Cancelled orders contained stale ETA/carrier fields
- **Reproduce:** Ask when `ORD-1004` will arrive.
- **Root cause:** The mock snapshot intentionally retains historical carrier/ETA fields after cancellation.
- **Fix:** `OrderLookup` clears stale carrier/ETA information for cancelled and returned orders and returns the current safe status message.
- **Regression:** `test_cancelled_order_drops_stale_eta`.

### 3. Follow-up delivery questions could lose the previous order ID
- **Reproduce:** Ask `Where is ORD-1007?`, then `When will it arrive?`.
- **Root cause:** An early router only recognized order identifiers present in the latest user turn.
- **Fix:** Session state now stores `last_order_id`, and status follow-ups explicitly reuse it in the model input.
- **Regression:** session-routing guard coverage and the multi-turn evaluation case.

### 4. Malformed order IDs could fall through to RAG
- **Reproduce:** Ask `Please check ORD-10XX`.
- **Root cause:** The first order-ID regex only recognized valid four-digit IDs, so malformed candidates were not classified as order input.
- **Fix:** Detect `ORD-...` candidates separately and return a deterministic validation response without a tool call.
- **Regression:** `test_malformed_order_id_is_rejected_without_lookup`.

### 5. Genuine source conflict could be silently resolved by the model
- **Reproduce:** Ask whether the Breeze Tumbler body can go in a dishwasher.
- **Root cause:** Two active official customer sources deliberately disagree.
- **Fix:** Detect the conflict pattern, expose both relevant sources, refuse to silently choose, and provide the safest interim guidance with human confirmation.
- **Regression:** the supplied `genuine-active-source-conflict` evaluation case.

## Known limitations

- Retrieval uses local lexical TF-IDF rather than embeddings. This is a deliberate small-corpus tradeoff for auditability and determinism.
- Session memory is process-local and is cleared on restart.
- The agent has only an order lookup tool; it cannot actually refund, cancel, replace, or modify orders.
- The behavior evaluator uses deterministic checks rather than a second LLM judge; semantic grading remains intentionally conservative.
- A final verified API-backed score requires a valid OpenAI API key and execution on a local machine or CI runner.

## AI coding tools disclosure

Development assistance used ChatGPT with GitHub-connected repository access to inspect the assignment, design the architecture, draft code/tests, review edge cases, and revise the implementation.

One concrete incomplete AI-generated suggestion occurred in the first implementation: all positively scored retrieval results were initially eligible to appear as customer-visible sources. That was unsafe because internal/legacy passages can be relevant without being authoritative. The design was corrected to separate retrieval evidence from customer-safe source exposure and covered with regression tests.

## Demo recording

The assignment requires a 2–4 minute GIF or video embedded in the README. The repository includes the application and a reproducible recording checklist, but an actual recording must be captured from the running local application because it must show real API-backed behavior rather than a fabricated transcript.

See `demo/recording-checklist.md` for the exact five-scene sequence and commands. After recording, embed the resulting GIF/video in this section.

## Submission checklist

- [x] Application source code
- [x] RAG over supplied Markdown corpus
- [x] Metadata-aware document precedence
- [x] Safe order lookup
- [x] Multi-turn session memory
- [x] Prompt/content safety
- [x] Visible-case evaluation coverage
- [x] Five original evaluation cases
- [x] Deterministic regression tests
- [x] Debug observability
- [x] CLI
- [x] Simple web UI
- [x] `.env.example` and secret-safe `.gitignore`
- [x] Architecture/setup/run documentation
- [x] Bug diary
- [ ] Verified API-backed baseline/final scores
- [ ] Real 2–4 minute demo GIF/video embedded in README
