import asyncio
import json
from typing import Any, AsyncIterator

import httpx


class OllamaUnavailable(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout_seconds: float, max_concurrency: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = httpx.Timeout(timeout_seconds, connect=10.0)
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def generate(self, prompt: str, system: str, *, stream: bool = False) -> str | AsyncIterator[str]:
        payload: dict[str, Any] = {
            "model": self.model,
            "system": system,
            "prompt": prompt,
            "stream": stream,
            "options": {"temperature": 0.1},
        }
        if stream:
            return self._stream(payload)
        async with self.semaphore:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(f"{self.base_url}/api/generate", json=payload)
                    response.raise_for_status()
                    return response.json().get("response", "")
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                raise OllamaUnavailable("Ollama is unavailable or still loading the model") from exc
            except httpx.HTTPStatusError as exc:
                raise OllamaUnavailable(f"Ollama returned HTTP {exc.response.status_code}") from exc

    async def _stream(self, payload: dict[str, Any]) -> AsyncIterator[str]:
        async with self.semaphore:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line:
                                data = json.loads(line)
                                if data.get("response"):
                                    yield data["response"]
                                if data.get("done"):
                                    break
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                raise OllamaUnavailable("Ollama stream timed out or became unavailable") from exc
            except httpx.HTTPStatusError as exc:
                raise OllamaUnavailable(f"Ollama returned HTTP {exc.response.status_code}") from exc
