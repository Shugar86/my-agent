import asyncio
import litellm


class ContextCompressor:
    def __init__(self, llm_gateway, max_tokens=4000, threshold_ratio=0.75):
        self.llm = llm_gateway
        self.max_tokens = max_tokens
        self.threshold_ratio = threshold_ratio

    def needs_compression(self, messages):
        total_tokens = sum(self._estimate_tokens(m) for m in messages)
        return total_tokens > self.max_tokens * self.threshold_ratio

    # ------------------------------------------------------------------
    # Synchronous API (for backward compat in non-async contexts)
    # ------------------------------------------------------------------
    def compress(self, messages, keep_last=4):
        if len(messages) <= keep_last:
            return messages

        to_compress = messages[1:-keep_last]
        system_msg = messages[0]
        recent_msgs = messages[-keep_last:]

        combined = self._format_messages(to_compress)
        summary = self._summarize_sync(combined)

        compressed = [system_msg, {"role": "system", "content": f"Summary of earlier conversation: {summary}"}]
        compressed.extend(recent_msgs)

        return compressed

    def _summarize_sync(self, text):
        try:
            response = litellm.completion(
                model=self.llm.primary,
                messages=[
                    {"role": "system", "content": "Summarize this conversation in 3-5 sentences. Keep key decisions and context."},
                    {"role": "user", "content": text[:8000]},
                ],
                api_key=self.llm.api_key,
                max_tokens=500,
            )
            return response.choices[0].message.content
        except Exception:
            return text[:2000]

    # ------------------------------------------------------------------
    # Async-native API
    # ------------------------------------------------------------------
    async def compress_async(self, messages, keep_last=4):
        if len(messages) <= keep_last:
            return messages

        to_compress = messages[1:-keep_last]
        system_msg = messages[0]
        recent_msgs = messages[-keep_last:]

        combined = self._format_messages(to_compress)
        summary = await self._summarize_async(combined)

        compressed = [system_msg, {"role": "system", "content": f"Summary of earlier conversation: {summary}"}]
        compressed.extend(recent_msgs)

        return compressed

    async def _summarize_async(self, text):
        try:
            response = await litellm.acompletion(
                model=self.llm.primary,
                messages=[
                    {"role": "system", "content": "Summarize this conversation in 3-5 sentences. Keep key decisions and context."},
                    {"role": "user", "content": text[:8000]},
                ],
                api_key=self.llm.api_key,
                max_tokens=500,
            )
            return response.choices[0].message.content
        except Exception:
            return text[:2000]

    def _format_messages(self, messages):
        parts = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if content:
                parts.append(f"[{role}]: {content}")
        return "\n".join(parts)

    def _estimate_tokens(self, message):
        content = message.get("content", "")
        if not content:
            return 0
        return len(content.split()) * 1.3
