"""
Base async HTTP API client with retry logic.
"""

import asyncio
from typing import Any, Optional

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from config.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

_DEFAULT_HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
    "X-Requested-With": "XMLHttpRequest",
}


class APIClient:
    """
    Thin async wrapper around httpx with automatic retries and
    shared session management.
    """

    def __init__(self, config: Config) -> None:
        self._config = config
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._config.BASE_URL,
                headers=_DEFAULT_HEADERS,
                timeout=httpx.Timeout(30.0),
                follow_redirects=True,
            )
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True,
    )
    async def get(self, path: str, params: Optional[dict] = None) -> Any:
        """
        Perform a GET request. Returns parsed JSON or raw text.
        Raises httpx.HTTPStatusError on non-2xx responses.
        """
        client = await self._get_client()
        logger.debug(f"GET {path} params={params}")
        response = await client.get(path, params=params)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "json" in content_type:
            return response.json()
        return response.text

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
