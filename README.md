# Resolve RAG — India Consumer Refund Guide

An educational RAG portfolio project for navigating everyday online-shopping complaints in India. Find relevant official-information summaries, optionally ask an AI to explain them, and prepare an editable complaint draft.

**Status:** V1 learning prototype for local or small private demos. Public source code does not mean a production-ready public service. It does **not** determine refund eligibility or retailer deadlines, submit complaints, or offer legal advice. This is an independent project, not affiliated with the National Consumer Helpline.

## The problem

When a purchase or refund goes wrong, consumers must find the right complaint channel, understand the process, and explain their issue clearly. Resolve demonstrates a source-backed alternative to a chatbot that confidently invents return windows or promises refunds.

## How it works

1. Load reviewed, original summaries of official consumer guidance.
2. Normalize a question and rank matching summaries using BM25-style keyword retrieval.
3. Display the retrieved evidence, or optionally give it to an OpenAI model to compose an answer.
4. Check generated citation IDs and fall back to evidence if the request or validation fails.
5. Show the original source links and let the user prepare a local complaint draft.

**Stack:** Python 3.11 · Streamlit · Python standard-library retrieval and HTTP client · optional OpenAI API · unittest · Docker.

**Start learning:** [Statement-by-statement code walkthrough](WALKTHROUGH.md).

## What is actually included

- Three original factual summaries based on two National Consumer Helpline pages, reviewed September 30, 2026. These are not copied policy documents or quotations.
- English keyword retrieval using a BM25-style score. No embeddings, vector database, crawler or document upload in this version.
- Evidence-only mode works locally without credentials and without sending questions to an AI service. This mode is retrieval, **not generative RAG**.
- Optional OpenAI mode supplies retrieved summaries to the model: this is the generative RAG path. It requires your own API access and may cost money.
- Source links, review dates, missing-evidence handling, an editable deterministic complaint draft, and offline tests.

The first scope is narrower than the long-term proposal: general complaint guidance, not retailer-specific advice. A three-summary corpus is sufficient to demonstrate the plumbing, not to prove broad consumer usefulness.

## Run on Windows / PowerShell

Clone the public repository, then enter its directory:

```powershell
git clone https://github.com/ravirocko315/resolve-rag.git
cd resolve-rag
```

Create an isolated environment, install dependencies, run tests, and start the app:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

Open http://localhost:8501. Press Ctrl+C to stop the server. On macOS/Linux the virtual-environment interpreter is `.venv/bin/python` instead.

Read `WALKTHROUGH.md` alongside the code. The guide follows every executable statement, explains multi-line statements together, and includes the tests and configuration files.

## Optional AI configuration

The app reads `OPENAI_API_KEY` and `OPENAI_MODEL` from its server process environment. Set them using your local environment or your deployment platform's secret manager. `.env.example` documents names only: copying it to `.env` does not load it. Do not send credentials in chat, commit them, bake them into Docker, or include them in screenshots.

Choose a model available to your OpenAI account that supports Chat Completions and `max_completion_tokens`. Restart the server after setting environment variables. The checkbox remains off by default. When explicitly enabled, a question and the retrieved public summaries are sent to OpenAI. A configured variable is not proof of valid credentials or model access. Missing configuration, timeouts, malformed responses and invalid citation IDs fall back to local summaries.

Citation checks verify identifiers only, not truth or whether a passage supports every sentence. Prompt-injection resistance is a precaution, not a security guarantee. No live provider call is part of the automated tests.

## Docker

```powershell
docker build -t resolve-v1:local .
docker run --rm -p 127.0.0.1:8501:8501 resolve-v1:local
```

Open http://localhost:8501. Localhost binding avoids exposing the demo to your LAN. The container runs as a nonroot user and supplies an HTTP health check. For optional AI, set the variables on the host first and use `-e OPENAI_API_KEY -e OPENAI_MODEL` before the image name. Never paste secret values directly into a shared command or Dockerfile.

The direct Streamlit version is pinned, but transitive dependencies and the Python base-image tag are not fully locked. Before a production release, capture a tested dependency lock and immutable image digest. This is repeatable packaging, not a guarantee of bit-for-bit builds.

## Before an internet-facing launch

This version is intended for local or small private use. A public production launch still needs:

1. Authentication, per-user rate limits, provider budgets and abuse protection.
2. HTTPS, WebSocket-capable hosting, secrets management, monitoring and rollback.
3. A reviewed, permitted retailer-policy corpus with effective dates, exclusions and update ownership.
4. Evaluation questions with expected sources and human review of claim support.
5. Tests for conflicting/outdated policies, regional ambiguity and adversarial inputs.
6. Hosting/provider privacy review; no sensitive real consumer data in demos.

The app writes no conversation database. Streamlit retains session state in server memory; provider and hosting retention policies still apply. Do not interpret this as a complete privacy guarantee.

## Sources and scope

- https://consumerhelpline.gov.in/ — contact channels.
- https://consumerhelpline.gov.in/public/about — complaint process and limitations.

The official site's reproduction notice is why this repository contains original factual summaries, not a scraped copy. Review any expansion for access and reuse permissions. Never invent a retailer's return window. Source review dates describe our review, not when an underlying policy became effective.

## Files

| File | Responsibility |
|---|---|
| `app.py` | Interface and session state |
| `core.py` | Loading, retrieval, evidence, optional generation, drafts |
| `data/sources.json` | Reviewed source summaries |
| `test_core.py` | Offline retrieval/error/citation tests |
| `test_app.py` | Streamlit question-and-draft integration test |
| `requirements.txt` | Direct dependency |
| `Dockerfile` | Container packaging |
| `.dockerignore`, `.gitignore` | Exclusion rules |
| `.env.example` | Environment-variable names |
| `WALKTHROUGH.md` | Code explanations |

## Troubleshooting

- **Port already in use:** use `--server.port=8502`, or Docker mapping `127.0.0.1:8502:8501`.
- **Module missing:** run installation and Streamlit using the same `.venv` interpreter.
- **No sources:** check that `data/sources.json` is valid JSON and every record has the required fields.
- **AI unavailable:** check provider access and environment settings privately; the app intentionally hides raw API errors because they may expose sensitive information.
- **Unhelpful evidence:** this corpus is deliberately small. More relevant reviewed sources, not a more confident prompt, are the next improvement.

## Verification performed — September 30, 2026

- Installed successfully in a fresh Windows Python 3.11 virtual environment.
- All 12 unittest tests passed, including the headless Streamlit question-and-draft flow.
- Docker image built successfully and ran as the configured nonroot user.
- Local container health endpoint returned `ok`; Docker reported `healthy`.
- Retrieval and the headless question-submission flow also passed inside the Linux container.
- No real OpenAI call, public-cloud deployment, load test or independent security audit was performed.

These checks describe the initial development environment; cloning this repository does not start a server. Follow the run instructions above to launch your own local preview. No hosted demo is currently provided.

## Roadmap

- Expand the permitted, reviewed corpus with retailer-specific policies and effective dates.
- Add a retrieval evaluation set and claim-support reviews before comparing embedding or hybrid search.
- Improve handling of ambiguous questions, jurisdictions and stale sources.
- Add authentication, request limits and cost controls before offering a public AI endpoint.

## Development notes

Built with AI-assisted development and accompanied by a detailed walkthrough so the implementation can be studied, tested and extended. The current tests exercise offline behavior and mocked provider responses; they are not evidence of real-model accuracy.
