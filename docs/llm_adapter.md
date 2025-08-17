# LLM Adapter Design Notes

The adapter exposes a single `generate` entry point which normalises LangChain's
various call styles.  At construction the adapter detects the underlying
backend and stores the appropriate callable.  This keeps the runtime hot path
small and avoids version specific branches during inference.

A special `model_name="fake-list"` uses an internal stub, no LangChain import.
Production backends require `api_key`. Unknown keys raise `ValueError`.

Example:
```python
llm = LangChainLLM({"model_name": "fake-list", "responses": ["ok"]})
llm.generate("ping")  # -> "ok"
```
