# Scloda Agent Hardening Checklist

Status as of July 22, 2026.

## Applied now

- [x] Better default OpenRouter model selection.
- [x] Model fallback chain if the primary model fails.
- [x] OpenRouter headers configurable from `.env` (`HTTP-Referer`, `X-Title`).
- [x] Input screening for obvious prompt-injection attempts.
- [x] Input screening for clearly out-of-scope requests.
- [x] Sanitized conversation history before sending it back to the model.
- [x] Tool argument validation and normalization.
- [x] Hard caps on lookback windows for market tools.
- [x] Date-aware tool metadata (`as_of`, freshness, market timezone).
- [x] Explicit no-live-data payloads instead of silent failures.
- [x] Historical/contextual fallback path when live data is unavailable.
- [x] Response post-processing to add missing date context.
- [x] Response post-processing to disclose when live data is unavailable.
- [x] Confidence score returned with chat responses.
- [x] Trace ID returned with chat responses.
- [x] Local regression harness for guardrail behavior.
- [x] Persistent trace storage in Postgres for Scloda chats.
- [x] Admin observability summary and recent trace endpoints.
- [x] Lightweight judge-model pass for retrieved/tool-grounded answers.
- [x] DB-backed retrieval cache with embeddings when available.
- [x] Task-based routing with tool allowlists by intent.
- [x] Redis-backed circuit breakers for tools and model retries.
- [x] Human review queue persisted in Postgres.
- [x] Lightweight classifier for scope, safety, and task type.
- [x] Seed labeled conversation dataset for classifier bootstrap.
- [x] Capability tree / Quantum Lab seed persisted in Postgres.
- [x] Automatic knowledge retrieval for DB / dataset / internal-source questions.
- [x] Manual knowledge reindex script and admin rebuild endpoint.

## Intentionally disabled today

- [ ] External eval platform such as Langfuse, Phoenix, or Promptfoo in CI.
- [ ] Automatic hallucination detection against tool outputs.
- [ ] Subscription-aware gating for advanced Scloda capabilities.

## Recommended next steps

### Short term

- [ ] Add a small curated dataset of real Scloda failures and expected answers.
- [ ] Add CI execution for `scripts/run_scloda_guardrail_checks.py`.
- [ ] Tighten judge criteria specifically for numeric answers with strict source/date checks.
- [ ] Add a small admin UI page on top of the new summary/trace endpoints.
- [ ] Decide whether judge pass should run on every answer or stay selective for cost control.

### Medium term

- [ ] Add Langfuse or Phoenix only if the team later wants external observability beyond Postgres-backed traces.
- [ ] Add Promptfoo or equivalent only if the team later wants formal prompt regression in CI.
- [ ] Split prompts by task type: chat, chart insights, model analysis, news analysis.
- [ ] Add a more explicit answer schema: answer, source, as_of, confidence, caveats.

### Pending by product choice

- [ ] Lightweight Charts upgrades.
- [ ] ECharts research dashboards.
- [ ] Premium charting evaluation (TradingView Advanced Charts).

## Not pending

- `ranking`, `wallets`, and `positions` are not treated as active Scloda launch blockers in the current product direction.
