import json
import os
from typing import Any, Dict, List, Mapping, Optional, Union

import httpx
from config.logger import logger


class RequestForwarderError(Exception):
    """
    Custom exception for handling RequestForwarder-specific errors.

    Attributes:
        original_exception: The original exception that was caught, if any.
    """

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.original_exception = original_exception


class RequestForwarder:
    """
    A class to forward HTTP requests to a specified base URL.

    Handles request construction, execution, and basic error handling using httpx.
    Manages an httpx.Client instance for connection pooling and configuration.

    Usage:
        forwarder = RequestForwarder(base_url="https://api.example.com")
        async with forwarder as client: # Use async client
             response = await client.get("/users", params={"page": 1})
             # or sync:
             response = forwarder.get("/users", params={"page": 1}) # Uses internal sync client

        # Or without context manager (less efficient for multiple requests)
        response = RequestForwarder(base_url="...").get("/status")
    """

    def __init__(
        self,
        base_url: str,
        default_headers: Optional[Dict[str, str]] = None,
        default_timeout: float = 20.0,
    ):
        """
        Initializes the RequestForwarder instance.

        Sets up the base URL, default headers (potentially derived from `current_user`),
        and default timeout. It also initializes both synchronous and asynchronous
        httpx clients based on this configuration.

        Args:
            base_url: The root URL to which all requests will be forwarded. Must include
                      the scheme (e.g., "http://", "https://"). A trailing slash will be added
                      if missing.
            default_headers: A dictionary of headers to be included in every request.
                             If not provided and `current_user` is, Bitbucket-specific
                             headers will be generated.
            default_timeout: The default time in seconds to wait for a response before
                             raising a timeout error.
        """
        if not base_url.endswith("/"):
            base_url += "/"
        self.base_url = base_url
        self._default_timeout = default_timeout

        if default_headers:
            self._default_headers = default_headers
        else:
            self._default_headers = RequestForwarder.build_bitbucket_headers()

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
        Prepares the request arguments by combining default and custom headers/timeout.

        Args:
            headers: Custom headers to merge with default headers.
            timeout: Custom timeout to override the default timeout.

        Returns:
            Dictionary containing the prepared headers and timeout.
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
        params: Optional[Mapping[str, Union[str, int, float, bool]]] = None,
        body: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        **kwargs: Any,  # Allow passing other httpx args like 'files', 'cookies' etc.
    ) -> httpx.Response:
        """
        Makes a synchronous HTTP request.

        Args:
            method: HTTP method (e.g., 'GET', 'POST').
            path: URL path relative to the base_url.
            params: Dictionary of query string parameters.
            json: JSON serializable Python object to send in the request body.
            data: Dictionary, list of tuples, bytes, or file-like object for form data.
            headers: Dictionary of request-specific headers.
            timeout: Request-specific timeout in seconds.
            **kwargs: Additional arguments passed directly to httpx.Client.request.

        Returns:
            An httpx.Response object.

        Raises:
            RequestForwarderError: If the request fails due to connection issues,
                                   timeouts, or other httpx errors.
        """
        if not self._client:
            raise RuntimeError("Synchronous client not initialized. Provide one or use the default.")

        relative_path = path.lstrip("/")
        request_args = self._prepare_request_args(headers, timeout)

        logger.info("Forwarding %s request to path: %s", method, relative_path)
        try:
            response = self._client.request(
                method=method,
                url=relative_path,
                params=RequestForwarder._format_list_params(params),
                json=body,
                data=data,
                headers=request_args["headers"],
                timeout=request_args["timeout"],
                **kwargs,
            )
            response.raise_for_status()
            return response
        except httpx.TimeoutException as e:
            logger.error("Request timed out: %s %s - %s", method, relative_path, e)
            raise RequestForwarderError(f"Request timed out: {e}", original_exception=e) from e
        except httpx.RequestError as e:
            logger.error("Request failed: %s %s - %s", method, relative_path, e)
            raise RequestForwarderError(f"Request failed: {e}", original_exception=e) from e
        except Exception as e:
            logger.error(
                "An unexpected error occurred during request: %s %s",
                method,
                relative_path,
            )
            raise RequestForwarderError(f"An unexpected error occurred: {e}", original_exception=e) from e

    async def arequest(
        self,
        method: str,
        path: str,
        params: Optional[Mapping[str, Union[str, int, float, bool]]] = None,
        body: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Makes an asynchronous HTTP request.

        Args:
            method: HTTP method (e.g., 'GET', 'POST').
            path: URL path relative to the base_url.
            params: Dictionary of query string parameters.
            json: JSON serializable Python object to send in the request body.
            data: Dictionary, list of tuples, bytes, or file-like object for form data.
            headers: Dictionary of request-specific headers.
            timeout: Request-specific timeout in seconds.
            **kwargs: Additional arguments passed directly to httpx.AsyncClient.request.


        Returns:
            An httpx.Response object.

        Raises:
            RequestForwarderError: If the request fails due to connection issues,
                                   timeouts, or other httpx errors.
        """
        if not self._async_client:
            raise RuntimeError("Asynchronous client not initialized. Provide one or use the default.")

        relative_path = path.lstrip("/")
        request_args = self._prepare_request_args(headers, timeout)

        logger.info(
            "Forwarding async %s request to path: %s with params: %s, body: %s, data: %s",
            method,
            relative_path,
            params,
            body,
            data,
        )
        try:
            response = await self._async_client.request(
                method=method,
                url=relative_path,
                params=RequestForwarder._format_list_params(params),
                json=body,
                data=data,
                headers=request_args["headers"],
                timeout=request_args["timeout"],
                **kwargs,
            )
            response.raise_for_status()
            return response
        except httpx.TimeoutException as e:
            logger.error("Async request timed out: %s %s - %s", method, relative_path, e)
            raise RequestForwarderError(f"Async request timed out: {e}", original_exception=e) from e
        except httpx.RequestError as e:
            logger.error("Async request failed: %s %s - %s", method, relative_path, e)
            raise RequestForwarderError(f"Async request failed: {e}", original_exception=e) from e
        except Exception as e:
            logger.error(
                "An unexpected error occurred during async request: %s %s",
                method,
                relative_path,
            )
            raise RequestForwarderError(f"An unexpected async error occurred: {e}", original_exception=e) from e

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        """Sends a GET request."""
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        """Sends a POST request."""
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> httpx.Response:
        """Sends a PUT request."""
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> httpx.Response:
        """Sends a PATCH request."""
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        """Sends a DELETE request."""
        return self.request("DELETE", path, **kwargs)

    # --- Asynchronous HTTP Verb Methods ---

    async def aget(self, path: str, **kwargs: Any) -> httpx.Response:
        """Sends an asynchronous GET request."""
        return await self.arequest("GET", path, **kwargs)

    async def apost(self, path: str, **kwargs: Any) -> httpx.Response:
        """Sends an asynchronous POST request."""
        return await self.arequest("POST", path, **kwargs)

    async def aput(self, path: str, **kwargs: Any) -> httpx.Response:
        """Sends an asynchronous PUT request."""
        return await self.arequest("PUT", path, **kwargs)

    async def apatch(self, path: str, **kwargs: Any) -> httpx.Response:
        """Sends an asynchronous PATCH request."""
        return await self.arequest("PATCH", path, **kwargs)

    async def adelete(self, path: str, **kwargs: Any) -> httpx.Response:
        """Sends an asynchronous DELETE request."""
        return await self.arequest("DELETE", path, **kwargs)

    # --- Context Management ---

    def __enter__(self) -> "RequestForwarder":
        """Enter the synchronous runtime context."""
        if self._client:
            self._client.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Exit the synchronous runtime context."""
        if self._client:
            self._client.__exit__(exc_type, exc_value, traceback)

    async def __aenter__(self) -> "RequestForwarder":
        """Enter the asynchronous runtime context."""
        if self._async_client:
            await self._async_client.__aenter__()
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Exit the asynchronous runtime context."""
        if self._async_client:
            await self._async_client.__aexit__(exc_type, exc_value, traceback)

    def close(self) -> None:
        """Closes the underlying synchronous httpx client if owned by this instance."""
        if self._client and not self._client.is_closed:
            self._client.close()
            logger.info("Closed internally managed synchronous httpx client.")

    async def aclose(self) -> None:
        """Closes the underlying asynchronous httpx client if owned by this instance."""
        if self._async_client and not self._async_client.is_closed:
            await self._async_client.aclose()
            logger.info("Closed internally managed asynchronous httpx client.")

    # --- Helper Methods ---

    @staticmethod
    def build_bitbucket_headers() -> dict:
        """
        Constructs authentication headers for Bitbucket API requests.

        Args:

        Returns:
            Dictionary containing the formatted Bitbucket authentication headers.
        """
        return {
            "Authorization": f"Bearer {os.getenv('BITBUCKET_TOKEN')}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "bitbucket-mcp",
        }

    @staticmethod
    def _format_list_params(
        params: Optional[Mapping[str, Union[str, int, float, bool, List[Any]]]],
    ) -> Optional[Mapping[str, Union[str, int, float, bool, List[Any]]]]:
        """
        Formats query parameters where values are lists.

        If a parameter value is a list and its key does not end with '[]',
        it appends '[]' to the key. This is common in some web frameworks
        for array parameter handling (e.g., PHP).

        Args:
            params: The original dictionary of query parameters.

        Returns:
            A new dictionary with list parameter keys potentially formatted,
            or None if the input was None.
        """
        if params is None:
            return None

        is_string = False
        if isinstance(params, str):
            try:
                params = json.loads(params)
                is_string = True
            except json.JSONDecodeError:
                logger.info("params is not a stringified hash")
                return params

        formatted_params: Dict[str, Union[str, int, float, bool, List[Any]]] = {}
        for key, value in params.items():
            if isinstance(value, list) and not key.endswith("[]"):
                formatted_params[f"{key}[]"] = value
            elif isinstance(value, dict):
                for k, v in value.items():
                    if isinstance(v, list):
                        formatted_params[f"{key}[{k}][]"] = v
                    else:
                        formatted_params[f"{key}[{k}]"] = v
            else:
                formatted_params[key] = value
        return json.dumps(formatted_params) if is_string else formatted_params
