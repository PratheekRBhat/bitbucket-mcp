"""Unit tests for BaseClient HTTP operations."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx

from bitbucket_client.core.base_client import BaseClient, BaseClientError


class TestBaseClientInitialization:
    """Tests for BaseClient initialization."""

    def test_init_with_all_parameters(self):
        """Client initializes with base URL, headers, and timeout."""
        headers = {"X-Custom": "value"}
        client = BaseClient(
            base_url="https://api.example.com",
            headers=headers,
            timeout=30.0,
        )

        assert client.base_url == "https://api.example.com/"
        assert client._default_headers == headers
        assert client._default_timeout == 30.0

    def test_init_appends_trailing_slash(self):
        """Base URL automatically appends trailing slash if missing."""
        client = BaseClient(base_url="https://api.example.com")
        assert client.base_url == "https://api.example.com/"

    def test_init_keeps_existing_trailing_slash(self):
        """Base URL with trailing slash remains unchanged."""
        client = BaseClient(base_url="https://api.example.com/")
        assert client.base_url == "https://api.example.com/"

    def test_init_default_headers_empty(self):
        """Default headers are empty dict when not provided."""
        client = BaseClient(base_url="https://api.example.com")
        assert client._default_headers == {}

    def test_init_default_timeout(self):
        """Default timeout is 20.0 seconds."""
        client = BaseClient(base_url="https://api.example.com")
        assert client._default_timeout == 20.0


class TestBaseClientPrepareRequestArgs:
    """Tests for _prepare_request_args helper method."""

    def test_prepare_with_no_custom_args(self):
        """Returns default headers and timeout when no custom args provided."""
        client = BaseClient(
            base_url="https://api.example.com",
            headers={"Default": "header"},
            timeout=20.0,
        )

        args = client._prepare_request_args()

        assert args["headers"] == {"Default": "header"}
        assert args["timeout"] == 20.0

    def test_prepare_with_custom_headers(self):
        """Custom headers override default headers."""
        client = BaseClient(
            base_url="https://api.example.com",
            headers={"Default": "header", "Another": "value"},
        )

        args = client._prepare_request_args(headers={"Custom": "override", "Another": "new"})

        assert args["headers"]["Default"] == "header"
        assert args["headers"]["Custom"] == "override"
        assert args["headers"]["Another"] == "new"

    def test_prepare_with_custom_timeout(self):
        """Custom timeout overrides default timeout."""
        client = BaseClient(base_url="https://api.example.com", timeout=20.0)

        args = client._prepare_request_args(timeout=60.0)

        assert args["timeout"] == 60.0


class TestBaseClientSyncRequests:
    """Tests for synchronous HTTP request methods."""

    @patch("bitbucket_client.core.base_client.httpx.Client")
    def test_request_constructs_url_correctly(self, mock_client_class):
        """request() method correctly constructs URLs and handles leading slashes."""
        mock_instance = Mock()
        mock_response = Mock(spec=httpx.Response)
        mock_response.raise_for_status = Mock()
        mock_instance.request.return_value = mock_response
        mock_client_class.return_value = mock_instance

        client = BaseClient(base_url="https://api.example.com/")
        client.request("GET", "/users/123")

        # Verify the path had leading slash stripped
        call_args = mock_instance.request.call_args
        assert call_args[1]["url"] == "users/123"

    @patch("bitbucket_client.core.base_client.httpx.Client")
    def test_get_calls_request_with_correct_method(self, mock_client_class):
        """get() calls request() with GET method."""
        mock_instance = Mock()
        mock_response = Mock(spec=httpx.Response)
        mock_response.raise_for_status = Mock()
        mock_instance.request.return_value = mock_response
        mock_client_class.return_value = mock_instance

        client = BaseClient(base_url="https://api.example.com/")
        client.get("/test")

        call_args = mock_instance.request.call_args
        assert call_args[1]["method"] == "GET"

    @patch("bitbucket_client.core.base_client.httpx.Client")
    def test_post_calls_request_with_correct_method(self, mock_client_class):
        """post() calls request() with POST method."""
        mock_instance = Mock()
        mock_response = Mock(spec=httpx.Response)
        mock_response.raise_for_status = Mock()
        mock_instance.request.return_value = mock_response
        mock_client_class.return_value = mock_instance

        client = BaseClient(base_url="https://api.example.com/")
        client.post("/test")

        call_args = mock_instance.request.call_args
        assert call_args[1]["method"] == "POST"

    @patch("bitbucket_client.core.base_client.httpx.Client")
    def test_request_with_query_params(self, mock_client_class):
        """Query parameters are properly passed."""
        mock_instance = Mock()
        mock_response = Mock(spec=httpx.Response)
        mock_response.raise_for_status = Mock()
        mock_instance.request.return_value = mock_response
        mock_client_class.return_value = mock_instance

        client = BaseClient(base_url="https://api.example.com/")
        client.request("GET", "/test", params={"foo": "bar", "page": 1})

        call_args = mock_instance.request.call_args
        assert call_args[1]["params"] == {"foo": "bar", "page": 1}

    @patch("bitbucket_client.core.base_client.httpx.Client")
    def test_request_with_json_body(self, mock_client_class):
        """JSON body is serialized and sent."""
        mock_instance = Mock()
        mock_response = Mock(spec=httpx.Response)
        mock_response.raise_for_status = Mock()
        mock_instance.request.return_value = mock_response
        mock_client_class.return_value = mock_instance

        client = BaseClient(base_url="https://api.example.com/")
        json_data = {"name": "test", "value": 42}
        client.request("POST", "/test", json_body=json_data)

        call_args = mock_instance.request.call_args
        assert call_args[1]["json"] == json_data

    @patch("bitbucket_client.core.base_client.httpx.Client")
    def test_request_raises_for_status(self, mock_client_class):
        """raise_for_status() is called on response."""
        mock_instance = Mock()
        mock_response = Mock(spec=httpx.Response)
        mock_instance.request.return_value = mock_response
        mock_client_class.return_value = mock_instance

        client = BaseClient(base_url="https://api.example.com/")
        client.request("GET", "/test")

        mock_response.raise_for_status.assert_called_once()


class TestBaseClientAsyncRequests:
    """Tests for asynchronous HTTP request methods."""

    @pytest.mark.asyncio
    @patch("bitbucket_client.core.base_client.httpx.AsyncClient")
    async def test_arequest_constructs_url_correctly(self, mock_async_client_class):
        """arequest() method correctly constructs URLs."""
        mock_instance = AsyncMock()
        mock_response = Mock(spec=httpx.Response)
        mock_response.raise_for_status = Mock()
        mock_instance.request.return_value = mock_response
        mock_async_client_class.return_value = mock_instance

        client = BaseClient(base_url="https://api.example.com/")
        await client.arequest("GET", "/users/123")

        call_args = mock_instance.request.call_args
        assert call_args[1]["url"] == "users/123"

    @pytest.mark.asyncio
    @patch("bitbucket_client.core.base_client.httpx.AsyncClient")
    async def test_aget_calls_arequest_with_correct_method(self, mock_async_client_class):
        """aget() calls arequest() with GET method."""
        mock_instance = AsyncMock()
        mock_response = Mock(spec=httpx.Response)
        mock_response.raise_for_status = Mock()
        mock_instance.request.return_value = mock_response
        mock_async_client_class.return_value = mock_instance

        client = BaseClient(base_url="https://api.example.com/")
        await client.aget("/test")

        call_args = mock_instance.request.call_args
        assert call_args[1]["method"] == "GET"

    @pytest.mark.asyncio
    @patch("bitbucket_client.core.base_client.httpx.AsyncClient")
    async def test_apost_calls_arequest_with_correct_method(self, mock_async_client_class):
        """apost() calls arequest() with POST method."""
        mock_instance = AsyncMock()
        mock_response = Mock(spec=httpx.Response)
        mock_response.raise_for_status = Mock()
        mock_instance.request.return_value = mock_response
        mock_async_client_class.return_value = mock_instance

        client = BaseClient(base_url="https://api.example.com/")
        await client.apost("/test")

        call_args = mock_instance.request.call_args
        assert call_args[1]["method"] == "POST"


class TestBaseClientErrorHandling:
    """Tests for error handling in HTTP requests."""

    @patch("bitbucket_client.core.base_client.httpx.Client")
    def test_timeout_exception_wrapped_in_base_client_error(self, mock_client_class):
        """httpx.TimeoutException is caught and wrapped in BaseClientError."""
        mock_instance = Mock()
        mock_instance.request.side_effect = httpx.TimeoutException("Request timed out")
        mock_client_class.return_value = mock_instance

        client = BaseClient(base_url="https://api.example.com/")

        with pytest.raises(BaseClientError) as exc_info:
            client.request("GET", "/test")

        assert "Request timed out" in str(exc_info.value)
        assert isinstance(exc_info.value.original_exception, httpx.TimeoutException)

    @patch("bitbucket_client.core.base_client.httpx.Client")
    def test_request_error_wrapped_in_base_client_error(self, mock_client_class):
        """httpx.RequestError is caught and wrapped in BaseClientError."""
        mock_instance = Mock()
        mock_instance.request.side_effect = httpx.RequestError("Connection failed")
        mock_client_class.return_value = mock_instance

        client = BaseClient(base_url="https://api.example.com/")

        with pytest.raises(BaseClientError) as exc_info:
            client.request("GET", "/test")

        assert "Request failed" in str(exc_info.value)
        assert isinstance(exc_info.value.original_exception, httpx.RequestError)

    @patch("bitbucket_client.core.base_client.httpx.Client")
    def test_generic_exception_wrapped_in_base_client_error(self, mock_client_class):
        """Generic exceptions are caught and wrapped in BaseClientError."""
        mock_instance = Mock()
        mock_instance.request.side_effect = ValueError("Unexpected error")
        mock_client_class.return_value = mock_instance

        client = BaseClient(base_url="https://api.example.com/")

        with pytest.raises(BaseClientError) as exc_info:
            client.request("GET", "/test")

        assert "An unexpected error occurred" in str(exc_info.value)
        assert isinstance(exc_info.value.original_exception, ValueError)


class TestBaseClientErrorClass:
    """Tests for BaseClientError exception class."""

    def test_error_with_message_only(self):
        """BaseClientError can be instantiated with just a message."""
        error = BaseClientError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.original_exception is None

    def test_error_with_original_exception(self):
        """BaseClientError stores original_exception when provided."""
        original = ValueError("Original error")
        error = BaseClientError("Wrapped error", original_exception=original)

        assert str(error) == "Wrapped error"
        assert error.original_exception is original

    def test_error_can_be_raised_and_caught(self):
        """BaseClientError can be raised and caught."""
        with pytest.raises(BaseClientError) as exc_info:
            raise BaseClientError("Test error")

        assert str(exc_info.value) == "Test error"


class TestBaseClientContextManagers:
    """Tests for context manager support."""

    @patch("bitbucket_client.core.base_client.httpx.Client")
    def test_sync_context_manager_enter_exit(self, mock_client_class):
        """Sync context manager properly manages client lifecycle."""
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance

        client = BaseClient(base_url="https://api.example.com/")

        with client as ctx_client:
            assert ctx_client is client
            mock_instance.__enter__.assert_called_once()

        mock_instance.__exit__.assert_called_once()

    @pytest.mark.asyncio
    @patch("bitbucket_client.core.base_client.httpx.AsyncClient")
    async def test_async_context_manager_enter_exit(self, mock_async_client_class):
        """Async context manager properly manages async client lifecycle."""
        mock_instance = AsyncMock()
        mock_async_client_class.return_value = mock_instance

        client = BaseClient(base_url="https://api.example.com/")

        async with client as ctx_client:
            assert ctx_client is client
            mock_instance.__aenter__.assert_called_once()

        mock_instance.__aexit__.assert_called_once()
