# Migration Guide

## LangChainLLM configuration

- Accepted production keys: `model_name`, `api_key`, `endpoint`, `temperature`.
- Fake LLM keys: `model_name="fake-list"`, optional `responses`, `responses_mode` (`"cycle"` or `"pop"`).
- When no API key is supplied and `OPENAI_API_KEY` is unset, the adapter now
  defaults to a deterministic fake backend emitting `"fake-response"` and logs a
  warning. Set `require_real_backend=True` or environment variable
  `OMNDX_REQUIRE_REAL_BACKEND=1` to fail instead.

## CoreAgent

- Calls now execute with a hard timeout and automatic retries with jittered
  backoff. All backend exceptions are wrapped in `BackendError` preserving the
  original cause. Defaults for timeout, retries and backoff may now be
  configured via constructor kwargs or environment variables
  (`OMNDX_AGENT_TIMEOUT`, `OMNDX_AGENT_MAX_RETRIES`,
  `OMNDX_AGENT_BACKOFF_BASE`) and overridden per call with the same keys.

## ChatMemory

- The store now operates without `chromadb`; in that case embedding searches
  degrade to a ranked substring match ordered by frequency and position. A new
  ``is_semantic_enabled`` property reports whether vector search is active.

### Production vs CI

For CI environments omit `OPENAI_API_KEY` and leave `OMNDX_REQUIRE_REAL_BACKEND`
unset to exercise the deterministic fake backend. In production set
`OMNDX_REQUIRE_REAL_BACKEND=1` and provide a real API key to disable the fake
path.
