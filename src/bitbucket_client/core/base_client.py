from typing import Any, Dict, Mapping, Optional

import httpx
from bitbucket_client.config.logger import logger


class BaseClientError(Exception):
    """
    Custom exception for handling BaseClient-specific errors.

    Attributes:
        original_exception: The original exception that was caught, if any.
    """

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.original_exception = original_exception


class BaseClient:
    """
    A generic class to handle HTTP requests using httpx.

    Manages an httpx.Client instance for connection pooling and configuration.
    """

    def __init__(
        self,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 20.0,
    ):
        """
        Initializes the BaseClient instance.

        Args:
            base_url: The root URL for all requests.
            headers: A dictionary of headers to be included in every request.
            timeout: The default time in seconds to wait for a response.
        """
        if not base_url.endswith("/"):
            base_url += "/"
        self.base_url = base_url
        self._default_timeout = timeout
        self._default_headers = headers or {}

        self._client = httpx.Client(
            base_url=self.base_url,
            headers=self._default_headers,
            timeout=self._default_timeout,
        )

        self._async_client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._default_headers,
            timeout=self._default_timeout,
        )

    def _prepare_request_args(
        self, headers: Optional[Dict[str, str]] = None, timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Prepares request arguments by combining default and custom headers/timeout.
        """
        request_headers = self._default_headers.copy()
        if headers:
            request_headers.update(headers)

        request_timeout = timeout if timeout is not None else self._default_timeout

        return {
            "headers": request_headers,
            "timeout": request_timeout,
        }

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Mapping[str, Any]] = None,
        json_body: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Makes a synchronous HTTP request.
        """
        relative_path = path.lstrip("/")
        request_args = self._prepare_request_args(headers, timeout)
        json_data = kwargs.pop("json", json_body)

        logger.info("Forwarding %s request to path: %s", method, relative_path)
        try:
            response = self._client.request(
                method=method,
                url=relative_path,
                params=params,
                json=json_data,
                data=data,
                headers=request_args["headers"],
                timeout=request_args["timeout"],
                **kwargs,
            )
            response.raise_for_status()
            return response
        except httpx.TimeoutException as e:
            logger.error("Request timed out: %s %s - %s", method, relative_path, e)
            raise BaseClientError(f"Request timed out: {e}", original_exception=e) from e
        except httpx.RequestError as e:
            logger.error("Request failed: %s %s - %s", method, relative_path, e)
            raise BaseClientError(f"Request failed: {e}", original_exception=e) from e
        except Exception as e:
            logger.error(
                "An unexpected error occurred during request: %s %s",
                method,
                relative_path,
            )
            raise BaseClientError(f"An unexpected error occurred: {e}", original_exception=e) from e

    async def arequest(
        self,
        method: str,
        path: str,
        params: Optional[Mapping[str, Any]] = None,
        json_body: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Makes an asynchronous HTTP request.
        """
        relative_path = path.lstrip("/")
        request_args = self._prepare_request_args(headers, timeout)
        json_data = kwargs.pop("json", json_body)

        logger.info(
            "Forwarding async %s request to path: %s with params: %s, body: %s, data: %s",
            method,
            relative_path,
            params,
            json_body,
            data,
        )
        try:
            response = await self._async_client.request(
                method=method,
                url=relative_path,
                params=params,
                json=json_data,
                data=data,
                headers=request_args["headers"],
                timeout=request_args["timeout"],
                **kwargs,
            )
            response.raise_for_status()
            return response
        except httpx.TimeoutException as e:
            logger.error("Async request timed out: %s %s - %s", method, relative_path, e)
            raise BaseClientError(f"Async request timed out: {e}", original_exception=e) from e
        except httpx.RequestError as e:
            logger.error("Async request failed: %s %s - %s", method, relative_path, e)
            raise BaseClientError(f"Async request failed: {e}", original_exception=e) from e
        except Exception as e:
            logger.error(
                "An unexpected error occurred during async request: %s %s",
                method,
                relative_path,
            )
            raise BaseClientError(f"An unexpected async error occurred: {e}", original_exception=e) from e

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("DELETE", path, **kwargs)

    async def aget(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self.arequest("GET", path, **kwargs)

    async def apost(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self.arequest("POST", path, **kwargs)

    async def aput(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self.arequest("PUT", path, **kwargs)

    async def apatch(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self.arequest("PATCH", path, **kwargs)

    async def adelete(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self.arequest("DELETE", path, **kwargs)

    def __enter__(self) -> "BaseClient":
        self._client.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self._client.__exit__(exc_type, exc_value, traceback)

    async def __aenter__(self) -> "BaseClient":
        await self._async_client.__aenter__()
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        await self._async_client.__aexit__(exc_type, exc_value, traceback)
