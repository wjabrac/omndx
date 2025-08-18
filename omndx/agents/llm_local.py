class LangChainLLM:
    """Adapter over LangChain-compatible backends."""

    _TEST_KEYS = {"responses", "responses_mode"}
    _PROD_KEYS = {"model_name", "endpoint", "api_key", "temperature"}

    def __init__(self, config: Dict[str, Any], *, require_real_backend: bool | None = None):
        self.config: Dict[str, Any] = dict(config)
        self.backend: str
        self._llm: Any
        self._call: Callable[..., str]

        model_name = str(self.config.get("model_name", ""))
        endpoint = self.config.get("endpoint")
        api_key = self.config.get("api_key") or os.getenv("OPENAI_API_KEY")

        if require_real_backend is None:
            require_real_backend = os.getenv("OMNDX_REQUIRE_REAL_BACKEND") == "1"

        allowed = self._PROD_KEYS | (self._TEST_KEYS if model_name == "fake-list" else set())
        unknown = set(self.config) - allowed
        if unknown and model_name != "fake-list":
            raise ValueError(f"Unknown config keys: {sorted(unknown)}")

        if require_real_backend and (model_name == "fake-list" or not api_key):
            raise ValueError("[LangChainLLM] real backend required; set OPENAI_API_KEY")

        if model_name == "fake-list" or (not model_name and not api_key):
            allowed = {"model_name", "endpoint", "temperature", "responses", "responses_mode"}
            unknown = set(self.config) - allowed
            if unknown:
                raise ValueError(f"Unknown config keys: {sorted(unknown)}")
            responses = self.config.get("responses") or ["fake-response"]
            mode = str(self.config.get("responses_mode", "cycle"))
            if mode not in {"cycle", "pop"}:
                raise ValueError("responses_mode must be 'cycle' or 'pop'")
            self.backend = "fake-list"
            self._llm = FakeListLLM(responses=responses, mode=mode)
            self._call = self._llm.generate
            safe_ep = (endpoint[:5] + "...") if endpoint else None
            logger.warning(
                "[LangChainLLM] defaulting to fake backend model=%s endpoint=%s hint=set OPENAI_API_KEY",
                model_name or "None",
                safe_ep,
            )
            return

        if not api_key:
            raise ValueError("api_key required for production backends")
        extra = {k: v for k, v in self.config.items() if k not in {"model_name", "endpoint", "api_key"}}

        try:
            from langchain_openai import ChatOpenAI  # type: ignore
            self.backend = "langchain_openai.ChatOpenAI"
            self._llm = ChatOpenAI(model=model_name, base_url=endpoint, api_key=api_key, **extra)
            call = getattr(self._llm, "invoke", None) or getattr(self._llm, "predict", None) or self._llm
            self._call = call
        except Exception:
            from langchain_community.llms import OpenAI  # type: ignore
            self.backend = "langchain_community.llms.OpenAI"
            if endpoint:
                extra["openai_api_base"] = endpoint
            extra["openai_api_key"] = api_key
            if model_name:
                extra["model_name"] = model_name
            self._llm = OpenAI(**extra)
            self._call = getattr(self._llm, "invoke", None) or getattr(self._llm, "predict", None) or self._llm
            logger.warning("OpenAI backend is deprecated and will be removed in a future release", stacklevel=2)

        if os.getenv("OMNDX_LLM_DEBUG"):
            safe_ep = (endpoint[:5] + "...") if endpoint else None
            logger.debug("backend=%s model=%s endpoint=%s", self.backend, model_name, safe_ep)

    def generate(self, prompt: str, **kwargs: Any) -> str:
        start = time.perf_counter()
        result = self._call(prompt, **kwargs)
        duration = time.perf_counter() - start
        if os.getenv("OMNDX_LLM_DEBUG"):
            logger.debug("call backend=%s duration=%.3f", self.backend, duration)
        return str(result)

