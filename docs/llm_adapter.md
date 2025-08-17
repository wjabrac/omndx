# LLM Adapter Design Notes

The adapter exposes a single `generate` entry point which normalises LangChain's
various call styles.  At construction the adapter detects the underlying
backend and stores the appropriate callable.  This keeps the runtime hot path
small and avoids version specific branches during inference.

A special `model_name="fake-list"` enables an internal stub used for tests and
offline scenarios.  Production backends require an explicit API key and reject
unknown configuration keys to prevent accidental leakage of test parameters.
