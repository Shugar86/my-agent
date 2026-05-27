"""Async-native LLM Gateway with retry, jittered backoff, and graceful fallback."""
import asyncio
import logging
import litellm

from core.kimi_provider import apply_kimi_headers, extract_message_content, resolve_kimi_base_url
from core.retry_utils import async_jittered_backoff

logger = logging.getLogger(__name__)


class APIErrorClassifier:
    """Classify LiteLLM/OpenRouter errors for retry decisions."""

    @staticmethod
    def classify_error(error: Exception) -> tuple[str, bool]:
        """Returns (category, should_retry).

        Categories:
            - "rate_limit": 429, quota exhausted → retry
            - "auth": 401, invalid key → no retry
            - "server": 500, 503, 502 → retry
            - "timeout": request timeout → retry
            - "invalid_request": 400, 422 → no retry
            - "unknown": anything else → retry once
        """
        msg = str(error).lower()
        error_type = type(error).__name__.lower()

        # Overload detection (server-side overload, not rate limit)
        # NeuroAPI returns "слишком большая нагрузка, попробуйте позже" (503 overload)
        if any(x in msg for x in ["слишком большая нагрузка"]):
            return "overload", True

        # Rate limit detection
        if any(x in msg for x in ["429", "rate limit", "rate-limit", "quota", "too many requests", "попробуйте позже"]):
            return "rate_limit", True

        # Auth errors
        if any(x in msg for x in ["401", "authentication", "unauthorized", "invalid api key", "incorrect api key", "user not found"]):
            return "auth", False

        # Bad request / validation
        if any(x in msg for x in ["400", "bad request", "invalid_request", "validation", "unsupported"]):
            return "invalid_request", False

        # Server errors
        if any(x in msg for x in ["500", "502", "503", "504", "internal server error", "bad gateway", "service unavailable"]):
            return "server", True

        # Timeouts
        if any(x in msg for x in ["timeout", "timed out", "connection timed out", "read timed out"]):
            return "timeout", True

        # Content policy / safety
        if any(x in msg for x in ["content policy", "safety", "moderation", "blocked", "policy violation"]):
            return "policy", False

        # LiteLLM-specific errors
        if "litellm" in error_type:
            if "rate" in msg:
                return "rate_limit", True
            if "auth" in msg:
                return "auth", False

        return "unknown", True


class LLMGateway:
    """Async LLM Gateway with retry, jittered backoff, and graceful fallback."""

    def __init__(self, model_config):
        self.primary = model_config.get("primary", "openrouter/mistralai/mistral-large")
        self.fallback = model_config.get("fallback")
        self.api_key = model_config.get("api_key")
        self.base_url = model_config.get("base_url")
        self.fallback_api_key = model_config.get("fallback_api_key")
        self.fallback_base_url = model_config.get("fallback_base_url")
        self.params = model_config.get("params", {})
        self.max_retries = model_config.get("max_retries", 3)
        self.retry_base_delay = model_config.get("retry_base_delay", 5.0)
        self.retry_max_delay = model_config.get("retry_max_delay", 120.0)

    async def _try_fallback(self, kwargs, last_error):
        """Try fallback model if configured."""
        if not self.fallback:
            return None
        logger.info("Switching to fallback model: %s", self.fallback)
        try:
            kwargs["model"] = self.fallback
            if self.fallback_api_key:
                kwargs["api_key"] = self.fallback_api_key
            fb_base = resolve_kimi_base_url(self.fallback_api_key, self.fallback_base_url)
            if fb_base:
                kwargs["api_base"] = fb_base
            elif self.fallback_base_url:
                kwargs["api_base"] = self.fallback_base_url
            apply_kimi_headers(kwargs)
            response = await litellm.acompletion(**kwargs)
            return self._normalize_message(response.choices[0].message)
        except Exception as fallback_error:
            logger.error("Fallback model also failed: %s", fallback_error)
            return None

    async def chat(self, messages, tools=None, **extra_kwargs):
        """Send chat completion with automatic retry and fallback.

        - Overload (503): retry primary with long delays (spikes pass in 15-30s)
        - Other errors: retry primary up to max_retries
        - Fallback: only after ALL primary retries exhausted
        - Fallback also overloaded: retry primary again with longer wait
        """
        kwargs = self._build_kwargs(messages, tools, **extra_kwargs)
        last_error = None

        # Phase 1: Retry primary model
        overload_fast_fallback = False
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug("LLM call attempt %d/%d (model=%s)", attempt, self.max_retries, self.primary)
                response = await litellm.acompletion(**kwargs)
                return self._normalize_message(response.choices[0].message)
            except Exception as e:
                category, should_retry = APIErrorClassifier.classify_error(e)
                last_error = e
                logger.warning(
                    "LLM call failed (attempt %d/%d, model=%s, category=%s): %s",
                    attempt, self.max_retries, self.primary, category, e,
                )
                if not should_retry:
                    break
                # Overload → fast fallback (no long retries)
                if category == "overload":
                    logger.info("Primary model overloaded, switching to fallback immediately")
                    overload_fast_fallback = True
                    break
                if attempt < self.max_retries:
                    delay = self.retry_base_delay * (2 ** (attempt - 1))
                    await asyncio.sleep(min(delay, self.retry_max_delay))
                else:
                    logger.error("Max retries exhausted for primary model")

        # Phase 2: Try fallback model (different provider ideally)
        if self.fallback and last_error is not None:
            logger.info("Trying fallback model: %s", self.fallback)
            fallback_kwargs = self._build_kwargs(messages, tools, model=self.fallback, **extra_kwargs)
            for attempt in range(1, 3):  # 2 attempts on fallback
                try:
                    response = await litellm.acompletion(**fallback_kwargs)
                    return self._normalize_message(response.choices[0].message)
                except Exception as e:
                    category, should_retry = APIErrorClassifier.classify_error(e)
                    logger.warning("Fallback attempt %d failed (category=%s): %s", attempt, category, e)
                    last_error = e
                    if category == "overload":
                        # Fallback also overloaded → return error fast
                        logger.error("Fallback also overloaded, cannot complete request")
                        return self._make_error_response(
                            RuntimeError("Все провайдеры перегружены. Попробуйте позже.")
                        )
                    if not should_retry:
                        break

        if last_error:
            return self._make_error_response(last_error)

        return self._make_error_response(RuntimeError("Unexpected empty response from LLM"))

    async def _stream_fallback(self, kwargs, last_error):
        """Try streaming fallback with retry."""
        if not self.fallback:
            yield {"type": "error", "content": str(last_error or "Stream failed")}
            return
        logger.info("Stream fallback to model: %s", self.fallback)
        fallback_kwargs = self._build_kwargs(
            kwargs.get("messages", []),
            kwargs.get("tools"),
            model=self.fallback,
        )
        fallback_kwargs["stream"] = True
        for attempt in range(1, 3):
            try:
                response = await litellm.acompletion(**fallback_kwargs)
                async for chunk in response:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if delta:
                        token = delta.content or getattr(delta, "reasoning_content", None)
                        if token:
                            yield {"type": "token", "content": token}
                yield {"type": "done"}
                return
            except Exception as e:
                category, _ = APIErrorClassifier.classify_error(e)
                logger.warning("Stream fallback attempt %d failed (category=%s): %s", attempt, category, e)
                if category == "overload":
                    logger.error("Fallback stream also overloaded")
                    yield {"type": "error", "content": "Все провайдеры перегружены. Попробуйте позже."}
                    return
        yield {"type": "error", "content": str(last_error or "Stream failed")}

    async def chat_stream(self, messages, tools=None, **extra_kwargs):
        """Stream chat completion, yielding token deltas.

        Yields dicts: {"type": "token", "content": "..."}
                      {"type": "tool_call", "name": "...", "args": "..."}
                      {"type": "done"}
                      {"type": "error", "content": "..."}
        """
        kwargs = self._build_kwargs(messages, tools, **extra_kwargs)
        kwargs["stream"] = True

        last_error = None

        # Phase 1: Retry primary
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug("Stream LLM attempt %d/%d (model=%s)", attempt, self.max_retries, self.primary)
                response = await litellm.acompletion(**kwargs)
                tool_calls_buffer = {}
                async for chunk in response:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if delta is None:
                        continue
                    token = delta.content or getattr(delta, "reasoning_content", None)
                    if token:
                        yield {"type": "token", "content": token}
                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in tool_calls_buffer:
                                tool_calls_buffer[idx] = {"name": "", "args": ""}
                            if tc.function and tc.function.name:
                                tool_calls_buffer[idx]["name"] += tc.function.name
                            if tc.function and tc.function.arguments:
                                tool_calls_buffer[idx]["args"] += tc.function.arguments
                    if chunk.choices[0].finish_reason:
                        for tc in tool_calls_buffer.values():
                            if tc["name"]:
                                yield {"type": "tool_call", "name": tc["name"], "args": tc["args"]}
                        yield {"type": "done"}
                        return
                yield {"type": "done"}
                return
            except Exception as e:
                category, should_retry = APIErrorClassifier.classify_error(e)
                last_error = e
                logger.warning(
                    "Stream LLM failed (attempt %d/%d, model=%s, category=%s): %s",
                    attempt, self.max_retries, self.primary, category, e,
                )
                if not should_retry:
                    break
                if attempt < self.max_retries:
                    delay = self.retry_base_delay * (2 ** (attempt - 1))
                    if category == "overload":
                        delay = max(delay, 10.0)
                    await asyncio.sleep(min(delay, self.retry_max_delay))

        # Phase 2: Try fallback
        async for item in self._stream_fallback(kwargs, last_error):
            yield item

    @staticmethod
    def _normalize_message(message):
        """Ensure message.content is populated for reasoning-only models."""
        content = extract_message_content(message)
        if content and not getattr(message, "content", None):
            message.content = content
        return message

    def _build_kwargs(self, messages, tools=None, model: str | None = None, **extra_kwargs):
        target_model = model or self.primary
        kwargs = {
            "model": target_model,
            "messages": messages,
            **self.params,
            **extra_kwargs,
        }
        if model == self.fallback or (model is None and target_model == self.fallback):
            if self.fallback_api_key:
                kwargs["api_key"] = self.fallback_api_key
            fb_base = resolve_kimi_base_url(self.fallback_api_key, self.fallback_base_url)
            if fb_base:
                kwargs["api_base"] = fb_base
            elif self.fallback_base_url:
                kwargs["api_base"] = self.fallback_base_url
        else:
            if self.api_key:
                kwargs["api_key"] = self.api_key
            resolved_base = resolve_kimi_base_url(self.api_key, self.base_url)
            if resolved_base:
                kwargs["api_base"] = resolved_base
            elif self.base_url:
                kwargs["api_base"] = self.base_url
        if tools:
            kwargs["tools"] = tools
        return apply_kimi_headers(kwargs)

    @staticmethod
    def _make_error_response(error: Exception):
        """Create a mock message object with error content for graceful degradation."""
        class _ErrorMessage:
            def __init__(self, content):
                self.content = content
                self.role = "assistant"
                self.tool_calls = None

        category, _ = APIErrorClassifier.classify_error(error)
        error_msg = str(error)
        if len(error_msg) > 500:
            error_msg = error_msg[:500] + "..."

        content = (
            f"I encountered an error while processing your request.\n\n"
            f"**Error type:** {category}\n"
            f"**Details:** {error_msg}\n\n"
            f"Please try again in a moment, or check your API configuration if this persists."
        )
        return _ErrorMessage(content)

    def switch(self, model_config):
        self.primary = model_config.get("primary", self.primary)
        self.fallback = model_config.get("fallback", self.fallback)
        self.api_key = model_config.get("api_key", self.api_key)
        self.base_url = model_config.get("base_url", self.base_url)
        self.params = model_config.get("params", self.params)
        self.max_retries = model_config.get("max_retries", self.max_retries)
