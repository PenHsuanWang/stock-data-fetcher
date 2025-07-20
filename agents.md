# agents.md — *Codex* Engineering & Data Fetch Agent

## 1. Purpose & Scope

Define an AI agent system that: (1) interprets natural language developer or analyst requests, (2) plans multi‑step tasks (code authoring, refactoring, data retrieval), (3) safely invokes internal tools (stock data fetch functions, file I/O, code exec sandboxes), (4) returns structured, auditable results, and (5) adheres to OpenAI Assistants API paradigms (tools: function calling, file search / code interpreter when enabled). ([OpenAI 平台][4], [OpenAI 平台][5], [OpenAI 平台][6])

## 2. Historical Context & Deprecation Awareness

Legacy Codex inference models were deprecated (March 2023), so the agent must target current general or reasoning/coding models (e.g. `gpt-4.1`, `o3-mini`, `o4-mini`, or other tool‑enabled releases) rather than obsolete endpoints; design includes a *Model Abstraction Layer* to swap models without rewriting orchestration when OpenAI publishes deprecations. ([GitHub][1], [Visual Studio Magazine][2], [OpenAI 平台][7])

## 3. Goals & Success Criteria

**Primary goals:** high‑accuracy function argument generation, deterministic structured outputs, minimized hallucinated tool calls, resilient rate limit handling, transparent adjusted‑price semantics. **Success metrics:** ≥95% valid JSON schema conformance for tool calls (with strict mode), error retry latency < exponential policy cap, and zero unapproved shell operations. ([OpenAI 平台][8], [OpenAI][9], [OpenAI 平台][10])

## 4. Non‑Goals

Not a portfolio optimizer, not giving investment advice, not bypassing provider ToS, and not persisting secrets outside the secure configuration store—explicit guardrails to prevent misuse. ([OpenAI 平台][5], [OpenAI 平台][4])

## 5. Architecture Overview

Pattern: **Planner → Tool Executor → Synthesizer**. Planner uses model reasoning to choose functions; Executor layer performs deterministic Python operations (fetch history, write CSVs, generate diffs); Synthesizer merges raw outputs + rationale + disclaimers; optional *Critic* pass revalidates structured output before returning. ([OpenAI 社區][11], [OpenAI 社區][12], [OpenAI 社區][13])

## 6. Tool / Function Inventory

| Tool Name                      | Category       | Purpose                                                        | Key Notes                                                                        |
| ------------------------------ | -------------- | -------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `fetch_history`                | Data           | Download OHLCV (symbols, start/end, interval, adjust flags).   | Inclusive end logic; maps to yfinance wrapper. ([OpenAI 平台][14], [OpenAI 平台][6]) |
| `list_supported_intervals`     | Meta           | Enumerate allowed intervals & max lookback hints.              | Prevent invalid interval errors. ([OpenAI 平台][14], [OpenAI 平台][5])               |
| `write_csv_bundle`             | Output         | Persist per‑symbol frames in naming scheme.                    | Deterministic artifact traceability. ([OpenAI 平台][5], [OpenAI 平台][6])            |
| `summarize_dataset`            | QA             | Row counts, min/max dates, gaps, columns.                      | Aids post‑fetch validation. ([OpenAI 社區][11], [Reddit][15])                      |
| `generate_code_patch`          | Code           | Create or modify Python modules / tests.                       | Uses model coding capability. ([The Verge][16], [Business Insider][17])          |
| `run_tests`                    | QA             | Execute unit tests subset (sandbox).                           | Isolated interpreter / code interpreter tool. ([OpenAI 平台][4], [OpenAI 平台][5])   |
| `explain_symbol_normalization` | Explainability | Show how each input symbol normalized (e.g. `2330`→`2330.TW`). | Transparency reduces confusion. ([Medium][18], [OpenAI 平台][6])                   |

## 7. Function Schemas (JSON Schema / Strict Mode)

Use Assistants *function calling* with `strict: true` to force model conformance; enumerations reduce drift; required fields enforce argument completeness; optional arrays allow incremental refinement (e.g. adding columns). ([OpenAI 平台][8], [OpenAI][9], [OpenAI 平台][10])

```jsonc
{
  "name": "fetch_history",
  "description": "Download historical OHLCV for symbols (inclusive end date).",
  "strict": true,
  "parameters": {
    "type": "object",
    "properties": {
      "symbols": { "type": "array", "items": { "type": "string" }, "minItems": 1 },
      "start_date": { "type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$" },
      "end_date": { "type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$" },
      "interval": {
        "type": "string",
        "enum": ["1m","2m","5m","15m","30m","60m","90m","1h","1d","5d","1wk","1mo","3mo"]
      },
      "auto_adjust": { "type": "boolean", "default": true },
      "repair": { "type": "boolean", "default": false },
      "columns": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Subset columns (e.g. Close, Volume)"
      }
    },
    "required": ["symbols","start_date"]
  }
}
```

Structured output enforcement ensures downstream parsing reliability and reduces guard code. ([OpenAI][9], [OpenAI 平台][10])

## 8. Model Selection Strategy

Default: a cost‑efficient, tool‑capable model for routine planning (e.g. mid‑tier reasoning or coding‑optimized variant); escalate to a higher reasoning model when: (a) multi‑file refactor, (b) complex dependency graph summarization, (c) test failure triage. New reasoning models (e.g. `o3-mini`) offer faster structured reasoning; fallback policies maintain continuity during model unavailability. ([The Verge][16], [The Verge][19], [GitHub][1])

## 9. Deprecation & Version Policy

Maintain a `models.json` manifest with `active`, `deprecated_by`, `sunset_date`; nightly job compares OpenAI deprecation feed and marks internally‑approved alternates to avoid sudden outages. ([OpenAI 平台][7], [Visual Studio Magazine][2])

## 10. Prompt Layer Design

**System Prompt:** sets role (“coding & data acquisition assistant”), forbids investment advice, mandates citation or provenance reporting. **Developer Prompt:** enumerates available functions & argument guidelines. **User Prompt:** raw user request. Chain-of-thought internal; only final rationale summary returned. ([OpenAI 平台][6], [OpenAI 平台][5], [OpenAI 社區][13])

## 11. Planning Heuristics

Before calling tools: validate date patterns; expand relative intervals (“last 3 weeks”) to concrete ISO dates; cluster symbols to respect rate limits (batch size threshold dynamic); if user wants code modification, draft diff via `generate_code_patch` first, then request confirmation before `write_csv_bundle`. ([OpenAI 社區][11], [Reddit][15], [OpenAI 平台][20])

## 12. Execution Workflow

1. **Parse & Normalize** (symbols / dates).
2. **Decide Tools** (single vs composite).
3. **Call `fetch_history`** (strict schema).
4. **Call `summarize_dataset`** for QA.
5. If user requested saving, invoke `write_csv_bundle`.
6. **Synthesizer** adds disclaimers & next‑step guidance. ([OpenAI 平台][14], [OpenAI 平台][6], [OpenAI 平台][4])

## 13. Structured Output & Validation

Strict mode ensures JSON matches schema; post‑validation includes semantic checks (date range non‑empty, interval valid, symbol count limit) before dispatch; errors trigger a *self‑correction* planner re‑prompt advising minimal delta changes. ([OpenAI 平台][8], [OpenAI][9], [OpenAI 平台][10])

## 14. Rate Limiting & Throttling

Read OpenAI published limits and adapt concurrency (tokens per minute / requests per minute) while adjusting for dynamic Plus / Pro or Azure quotas; implement exponential backoff + jitter for 429 or network spikes. ([OpenAI 平台][20], [微軟學習][21], [OpenAI 社區][22])

## 15. External Data & Image / Code Tools

Assistants API supports Code Interpreter and File Search; enabling Code Interpreter allows dynamic parsing of downloaded CSVs for user quick stats without manual local execution; treat file tool operations as privileged steps requiring explicit user consent. ([OpenAI 平台][4], [OpenAI 平台][5])

## 16. Performance Tuning

Choose smaller reasoning models for simple argument formation (reduces latency) and escalate for multi‑function code generation; maintain batch threshold heuristics (e.g. > N symbols triggers chunking) to minimize upstream service pressure. ([The Verge][19], [The Verge][16])

## 17. Code Generation & Refactoring

Leverage modern coding / reasoning models (e.g. improved coding throughput vs older Codex) to produce diffs instead of full files; diffs reduce merge risk; include test stubs referencing affected modules. ([The Verge][16], [GitHub][1])

## 18. Error Taxonomy & Recovery

| Error                                                                                                                                               | Likely Cause          | Mitigation                                    |
| --------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- | --------------------------------------------- |
| Schema Validation                                                                                                                                   | Hallucinated arg name | Self‑repair prompt with explicit allowed keys |
| Rate Limit 429                                                                                                                                      | Burst activity        | Backoff + batch splitting                     |
| Empty Dataset                                                                                                                                       | Bad symbol / holiday  | Suggest interval or date shift                |
| Deprecation Failure                                                                                                                                 | Model removed         | Swap to fallback from manifest                |
| Tool Timeout                                                                                                                                        | Network stall         | Retry (bounded) then partial result summary   |
| Referenced best practices encourage iterative function planning and monitoring reasoning drift. ([OpenAI 社區][11], [OpenAI 社區][13], [OpenAI 社區][12]) |                       |                                               |

## 19. Security & Compliance

No secrets in user prompts; environment variables for API keys; disclaimers inserted on every financial data response to clarify informational nature; refuse trading recommendations to remain within safe usage guidelines. ([OpenAI 平台][5], [OpenAI 平台][4], [OpenAI 平台][6])

## 20. Logging & Observability

Log (request\_id, model, tokens\_in/out, tool\_calls\[], latency\_ms, retry\_count, rate\_limit\_headers snapshot) to enable capacity planning and debugging tool misuse. Rate metrics correlate with evolving usage/message limits environment to preempt throttling. ([OpenAI 平台][20], [OpenAI 社區][22], [The Verge][19])

## 21. Testing Strategy

* **Schema Tests:** Validate JSON definitions compile & required fields enforced.
* **Prompt Replay:** Golden user prompts produce stable tool call sequences.
* **Mutation Tests:** Inject invalid intervals to confirm rejection flow.
* **Latency Benchmarks:** Compare small vs reasoning model call times weekly.
* **Deprecation Simulation:** Force model removal to test fallback.
  Community best practices highlight iterative refinement to improve function selection fidelity. ([Reddit][15], [OpenAI 社區][11], [OpenAI 平台][6])

## 22. CI/CD Integration

Pre‑merge pipeline: run unit tests, schema lint, sample assistant dry‑run (no external calls for determinism); nightly job triggers live integration tests within rate limits. ([OpenAI 平台][20], [微軟學習][21])

## 23. Versioning & Change Control

Semantic version for agent spec (`agents.md`): increment MINOR when adding tools; MAJOR when altering existing schema shape; patch for documentation or non‑breaking prompt tweaks; record upstream model migrations. ([OpenAI 平台][7], [Visual Studio Magazine][2])

## 24. Observed Ecosystem Trends

Increased availability of reasoning models and CLI / local agent tooling (open source codex CLI) motivates modular model adapter; news indicates ongoing improvements in coding performance and research tool rate limit adjustments. ([GitHub][1], [The Verge][16], [The Verge][19])

## 25. Roadmap

**Short term:** Retry abstraction, interval lookback heuristics, diff‑aware code patch tool. **Mid term:** Automatic test generation from code changes, partial dataset streaming summarizer. **Long term:** Multi‑agent parallelization (task graph) and adaptive model selection using live performance metrics. ([OpenAI 社區][13], [The Verge][16], [GitHub][1])

## 26. Example Session Trace (Condensed)

User asks: “Get 2330 and AAPL daily close & volume for last month and save files.” Planner expands dates, normalizes `2330`→`2330.TW`, calls `fetch_history`, then `write_csv_bundle`, returns summary plus disclaimer. ([Medium][18], [OpenAI 平台][14], [OpenAI 平台][6])

## 27. Example Planner Prompt Snippet

“Given the user request: … Decide if data fetch, code change, or explanation. For fetch: produce a single `fetch_history` call with inclusive ISO dates. Validate intervals against allowed enum. If user asked to save, follow with `write_csv_bundle` using previous result context. Never speculate financial advice.” ([OpenAI 平台][6], [OpenAI 平台][14], [OpenAI 平台][5])

## 28. Example Self‑Repair Prompt

“If previous function call failed due to invalid parameter, propose corrected call using ONLY valid parameter names: … Provide updated JSON arguments matching schema.” ([OpenAI 社區][11], [Reddit][15])

## 29. Monitoring & Metrics

Track: tool\_call\_accuracy (% successful executions), avg\_planning\_tokens, function\_retry\_rate, schema\_noncompliance\_count, and time\_to\_first\_token across models to evaluate trade‑offs and plan upgrades. ([The Verge][16], [OpenAI 平台][20], [OpenAI 社區][22])

## 30. Appendix A: Additional Schemas

Include `write_csv_bundle` with required `output_path` & `file_format` enum to prepare for adding parquet/json later; strict schema ensures future extension without breaking existing parameters. ([OpenAI 平台][8], [OpenAI][9])

## 31. Appendix B: Rate Limit Backoff Policy

Initial delay 1s; multiplier 2; jitter ±20%; max attempts 5; abort and summarize partial results if still failing—aligned with general community recommendations to reduce thrash. ([OpenAI 平台][20], [Reddit][15])

## 32. Appendix C: Model Fallback Table

| Priority                                                                                                                     | Model                                    | Use Case                            | Fallback Trigger               |
| ---------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | ----------------------------------- | ------------------------------ |
| 1                                                                                                                            | High reasoning (e.g., latest tool model) | Multi-step planning                 | Latency SLA breach or quota    |
| 2                                                                                                                            | Mid-tier (fast)                          | Standard fetch + simple code edits  | Rate limit spikes or high cost |
| 3                                                                                                                            | Small / lightweight                      | Quick symbol normalization, retries | Global throttling              |
| Stay current with emerging reasoning / coding models for optimal trade‑offs. ([The Verge][19], [The Verge][16], [GitHub][1]) |                                          |                                     |                                |

## 33. Appendix D: Deprecation Checklist

Weekly cron: call deprecation endpoint feed / docs, diff against manifest, warn if active model scheduled for retirement; auto create ticket to update config. ([OpenAI 平台][7], [Visual Studio Magazine][2])

## 34. Appendix E: User Safety Statement Injection

Every financial data answer appends: “Data is informational, sourced via Yahoo Finance interfaces, may be delayed or incomplete; no investment advice.” (Enforced by post‑processor). ([OpenAI 平台][5], [OpenAI 平台][4], [OpenAI 平台][6])

## 35. Approval & Governance

Material changes (new external tool, relaxed safety rule, model swap) require two maintainer approvals and version bump; referenced against deprecation & best practice guidance for accountability. ([OpenAI 平台][7], [OpenAI 社區][11], [OpenAI 平台][6])

---

**End of `agents.md`** — This specification should evolve with OpenAI tool capabilities, new model releases, and internal performance telemetry. ([OpenAI 平台][4], [The Verge][16], [GitHub][1])

[1]: https://github.com/openai/codex?utm_source=chatgpt.com "openai/codex: Lightweight coding agent that runs in your terminal"
[2]: https://visualstudiomagazine.com/articles/2025/05/16/the-return-of-codex-ai-as-an-agent.aspx?utm_source=chatgpt.com "The Return of Codex AI — as an Agent - Visual Studio Magazine"
[3]: https://community.openai.com/t/can-i-still-access-openai-codex-2024/690893?utm_source=chatgpt.com "Can I still access OpenAI Codex 2024? - Prompting"
[4]: https://platform.openai.com/docs/assistants/overview?utm_source=chatgpt.com "Assistants API overview Beta - OpenAI Platform"
[5]: https://platform.openai.com/docs/assistants/tools/function-calling?utm_source=chatgpt.com "Assistants Function Calling - OpenAI API"
[6]: https://platform.openai.com/docs/guides/function-calling?utm_source=chatgpt.com "function calling docs - OpenAI Platform"
[7]: https://platform.openai.com/docs/deprecations/base-gpt-models?utm_source=chatgpt.com "Deprecations - OpenAI API"
[8]: https://platform.openai.com/docs/guides/structured-outputs?utm_source=chatgpt.com "Structured Outputs - OpenAI API"
[9]: https://openai.com/index/introducing-structured-outputs-in-the-api/?utm_source=chatgpt.com "Introducing Structured Outputs in the API - OpenAI"
[10]: https://platform.openai.com/docs/guides/function-calling/function-calling-with-structured-outputs?utm_source=chatgpt.com "function calling with structured output - OpenAI Platform"
[11]: https://community.openai.com/t/best-practices-for-improving-assistants-function-calling-reasoning-ability/596180?utm_source=chatgpt.com "Best Practices for Improving Assistants' Function calling Reasoning ..."
[12]: https://community.openai.com/t/how-does-function-calling-actually-work-for-the-assistants-api/641440?utm_source=chatgpt.com "How does function calling actually work for the Assistants API?"
[13]: https://community.openai.com/t/prompting-best-practices-for-tool-use-function-calling/1123036?utm_source=chatgpt.com "Prompting Best Practices for Tool Use (Function Calling)"
[14]: https://platform.openai.com/docs/assistants/tools/function-calling/quickstart?utm_source=chatgpt.com "function calling - OpenAI Platform"
[15]: https://www.reddit.com/r/OpenAI/comments/1f1p5o8/guide_to_function_calling_tool_use/?utm_source=chatgpt.com "Guide to Function Calling / Tool Use : r/OpenAI - Reddit"
[16]: https://www.theverge.com/news/603849/openai-o3-mini-launch-chatgpt-api-available-now?utm_source=chatgpt.com "OpenAI launches new o3-mini reasoning model with a free ChatGPT version"
[17]: https://www.businessinsider.com/openai-google-anthropic-ai-updates-gpt-gemini-claude-2025-3?utm_source=chatgpt.com "Here's what you need to know about OpenAI, Google and Anthropic's latest AI moves"
[18]: https://medium.com/%40bbkgull/mastering-openais-function-calling-a-guide-with-examples-d631a9bf151b?utm_source=chatgpt.com "Mastering OpenAI's Function Calling: A Guide with Examples"
[19]: https://www.theverge.com/news/656142/chatgpt-lightweight-deep-research-free-plus-team-pro?utm_source=chatgpt.com "ChatGPT is getting a 'lightweight' version of its deep research tool"
[20]: https://platform.openai.com/docs/guides/rate-limits?utm_source=chatgpt.com "Rate limits - OpenAI API"
[21]: https://learn.microsoft.com/en-us/azure/ai-foundry/openai/quotas-limits?utm_source=chatgpt.com "Azure OpenAI in Azure AI Foundry Models quotas and limits"
[22]: https://community.openai.com/t/chatgpt-plus-user-limits-valid-for-2025/1149656?utm_source=chatgpt.com "ChatGPT Plus User Limits, valid for 2025"
