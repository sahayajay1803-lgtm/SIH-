import asyncio
import json
from typing import Any, AsyncIterator

import httpx


class LLMUnavailable(RuntimeError):
    pass


def parse_json_object(raw: str) -> dict[str, Any]:
    """Parse strict JSON or JSON wrapped in a markdown fence/prose."""
    candidate = raw.strip()
    if candidate.startswith("```"):
        candidate = candidate.split("\n", 1)[-1]
        candidate = candidate.rsplit("```", 1)[0].strip()
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        start, end = candidate.find("{"), candidate.rfind("}")
        if start < 0 or end <= start:
            raise
        value = json.loads(candidate[start : end + 1])
    if not isinstance(value, dict):
        raise json.JSONDecodeError("Expected a JSON object", candidate, 0)
    return value


class OllamaCloudClient:
    """OpenAI-compatible Ollama Cloud client with bounded concurrent requests."""

    def __init__(self, base_url: str, api_key: str, model: str, timeout_seconds: float, max_concurrency: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = httpx.Timeout(timeout_seconds, connect=10.0)
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def status(self) -> dict[str, Any]:
        if not self.api_key:
            return {"available": False, "configured": False}
        return {"available": True, "configured": True, "provider": "ollama_cloud", "model": self.model}

    async def generate(self, prompt: str, system: str, *, stream: bool = False) -> str | AsyncIterator[str]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "stream": stream,
        }
        if stream:
            return self._stream(payload)
        async with self.semaphore:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(self._endpoint, headers=self._headers, json=payload)
                    response.raise_for_status()
                    return self._content(response.json())
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                raise LLMUnavailable("Ollama Cloud timed out or is unavailable") from exc
            except httpx.HTTPStatusError as exc:
                raise LLMUnavailable(f"Ollama Cloud returned HTTP {exc.response.status_code}") from exc

    async def _stream(self, payload: dict[str, Any]) -> AsyncIterator[str]:
        async with self.semaphore:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    async with client.stream("POST", self._endpoint, headers=self._headers, json=payload) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if not line or line == "data: [DONE]":
                                continue
                            if line.startswith("data: "):
                                data = json.loads(line[6:])
                                delta = data.get("choices", [{}])[0].get("delta", {}).get("content")
                                if delta:
                                    yield delta
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                raise LLMUnavailable("Ollama Cloud stream timed out or is unavailable") from exc
            except httpx.HTTPStatusError as exc:
                raise LLMUnavailable(f"Ollama Cloud returned HTTP {exc.response.status_code}") from exc

    @property
    def _endpoint(self) -> str:
        return f"{self.base_url}/chat/completions"

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    @staticmethod
    def _content(data: dict[str, Any]) -> str:
        return data["choices"][0]["message"]["content"]