# Configuration

## LLM backends
- `OPENAI_API_KEY`: when set, `LangChainLLM` uses a real backend.
- `OMNDX_REQUIRE_REAL_BACKEND=1`: fail if a fake backend would be selected.
- `responses` and `responses_mode` (`cycle` or `pop`) configure the built-in fake backend.

## CoreAgent
- Defaults may be overridden via `OMNDX_AGENT_TIMEOUT`, `OMNDX_AGENT_MAX_RETRIES` and `OMNDX_AGENT_BACKOFF_BASE` or passed per call.

## Memory
- When `chromadb` is installed, `ChatMemory` performs semantic search. Otherwise it falls back to ranked substring search; `is_semantic_enabled` reports the active mode.
