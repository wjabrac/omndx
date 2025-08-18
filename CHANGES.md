# Changelog

## Unreleased
- LLM adapter warns and defaults to deterministic fake responses when no API key is present; set `require_real_backend=True` or `OMNDX_REQUIRE_REAL_BACKEND=1` to enforce real backends.
- CoreAgent now accepts timeout, retry and backoff overrides via kwargs or environment variables.
- ChatMemory falls back to ranked substring search and exposes `is_semantic_enabled`.
- Added `preflight.check` utility and documentation for configuration.
