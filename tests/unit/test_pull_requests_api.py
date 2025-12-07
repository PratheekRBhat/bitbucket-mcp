"""Unit tests for PullRequestsAPI methods."""

from unittest.mock import Mock, patch

import httpx
import pytest

from bitbucket_client.api.pull_requests import PullRequestsAPI
from bitbucket_client.core import BaseClientError
from bitbucket_client.models import (
    CreatePullRequestParams,
    DeclinePullRequestParams,
    GetPullRequestParams,
    GetPullRequestsParams,
    MergePullRequestParams,
    MergePullRequestSimpleParams,
    PullRequest,
)
from tests.fixtures.api_responses import (
    EMPTY_PULL_REQUEST_LIST,
    PULL_REQUEST_LIST_RESPONSE,
    PULL_REQUEST_MERGED,
    PULL_REQUEST_OPEN,
)


class TestPullRequestsAPIInitialization:
    """Tests for PullRequestsAPI initialization."""

    def test_stores_http_client_reference(self, mock_http_client):
        """API client stores reference to HttpClient."""
        api = PullRequestsAPI(http_client=mock_http_client)
        assert api.http_client is mock_http_client


class TestPullRequestsAPIGet:
    """Tests for get() method."""

    def test_get_constructs_correct_path(self, mock_http_client):
        """Constructs correct path: pullrequests/{pull_request_id}."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = PULL_REQUEST_OPEN
        mock_http_client.get = Mock(return_value=mock_response)

        api = PullRequestsAPI(http_client=mock_http_client)
        api.get(params=GetPullRequestParams(pull_request_id=42))

        mock_http_client.get.assert_called_once_with(path="pullrequests/42")

    def test_get_returns_pull_request_model(self, mock_http_client):
        """Returns PullRequest object with correct attributes."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = PULL_REQUEST_OPEN
        mock_http_client.get = Mock(return_value=mock_response)

        api = PullRequestsAPI(http_client=mock_http_client)
        result = api.get(params=GetPullRequestParams(pull_request_id=1))

        assert isinstance(result, PullRequest)
        assert result.id == 1
        assert result.title == "Implement user authentication"
        assert result.state == "OPEN"

    def test_get_handles_api_error(self, mock_http_client):
        """Handles API errors and re-raises BaseClientError."""
        mock_http_client.get = Mock(side_effect=BaseClientError("API error"))

        api = PullRequestsAPI(http_client=mock_http_client)

        with pytest.raises(BaseClientError):
            api.get(params=GetPullRequestParams(pull_request_id=999))


class TestPullRequestsAPIList:
    """Tests for list() method."""

    def test_list_constructs_correct_path(self, mock_http_client):
        """Constructs correct path: pullrequests."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = PULL_REQUEST_LIST_RESPONSE
        mock_http_client.get = Mock(return_value=mock_response)

        api = PullRequestsAPI(http_client=mock_http_client)
        api.list(params=GetPullRequestsParams(state="open"))

        mock_http_client.get.assert_called_once_with(path="pullrequests", params={"state": "OPEN"})

    def test_list_uppercases_state_parameter(self, mock_http_client):
        """Passes state parameter in uppercase (e.g., OPEN, MERGED)."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = PULL_REQUEST_LIST_RESPONSE
        mock_http_client.get = Mock(return_value=mock_response)

        api = PullRequestsAPI(http_client=mock_http_client)
        api.list(params=GetPullRequestsParams(state="merged"))

        call_args = mock_http_client.get.call_args
        assert call_args[1]["params"]["state"] == "MERGED"

    def test_list_returns_list_of_pull_requests(self, mock_http_client):
        """Returns list of PullRequest objects."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = PULL_REQUEST_LIST_RESPONSE
        mock_http_client.get = Mock(return_value=mock_response)

        api = PullRequestsAPI(http_client=mock_http_client)
        result = api.list(params=GetPullRequestsParams(state="open"))

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(pr, PullRequest) for pr in result)
        assert result[0].id == 1
        assert result[1].id == 4

    def test_list_handles_empty_response(self, mock_http_client):
        """Handles empty response (no pull requests)."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = EMPTY_PULL_REQUEST_LIST
        mock_http_client.get = Mock(return_value=mock_response)

        api = PullRequestsAPI(http_client=mock_http_client)
        result = api.list(params=GetPullRequestsParams(state="open"))

        assert result == []

    def test_list_handles_api_error(self, mock_http_client):
        """Handles API errors and re-raises BaseClientError."""
        mock_http_client.get = Mock(side_effect=BaseClientError("API error"))

        api = PullRequestsAPI(http_client=mock_http_client)

        with pytest.raises(BaseClientError):
            api.list(params=GetPullRequestsParams(state="open"))


class TestPullRequestsAPICreate:
    """Tests for create() method."""

    def test_create_constructs_correct_path(self, mock_http_client):
        """Constructs correct path: pullrequests."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = PULL_REQUEST_OPEN
        mock_http_client.post = Mock(return_value=mock_response)

        api = PullRequestsAPI(http_client=mock_http_client)

        params = CreatePullRequestParams(
            title="New PR",
            source_branch="feature",
            destination_branch="main",
        )
        api.create(params=params)

        # Get the first positional argument (path)
        call_args = mock_http_client.post.call_args
        assert call_args[0][0] == "pullrequests"

    def test_create_serializes_model_excluding_none(self, mock_http_client):
        """Serializes CreatePullRequest model to JSON (excluding None values)."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = PULL_REQUEST_OPEN
        mock_http_client.post = Mock(return_value=mock_response)

        api = PullRequestsAPI(http_client=mock_http_client)

        params = CreatePullRequestParams(
            title="New PR",
            source_branch="feature",
            destination_branch="main",
            description=None,  # Should be excluded
        )
        api.create(params=params)

        call_args = mock_http_client.post.call_args
        json_data = call_args[1]["json"]

        assert "title" in json_data
        assert "source" in json_data
        assert "destination" in json_data
        # None values should be excluded
        assert "description" not in json_data or json_data.get("description") is not None

    def test_create_returns_pull_request_model(self, mock_http_client):
        """Returns newly created PullRequest object."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = PULL_REQUEST_OPEN
        mock_http_client.post = Mock(return_value=mock_response)

        api = PullRequestsAPI(http_client=mock_http_client)

        params = CreatePullRequestParams(
            title="New PR",
            source_branch="feature",
            destination_branch="main",
        )
        result = api.create(params=params)

        assert isinstance(result, PullRequest)
        assert result.id == 1

    def test_create_handles_api_error(self, mock_http_client):
        """Handles API errors and re-raises BaseClientError."""
        mock_http_client.post = Mock(side_effect=BaseClientError("API error"))

        api = PullRequestsAPI(http_client=mock_http_client)

        params = CreatePullRequestParams(
            title="New PR",
            source_branch="feature",
            destination_branch="main",
        )

        with pytest.raises(BaseClientError):
            api.create(params=params)


class TestPullRequestsAPIMerge:
    """Tests for merge() method."""

    def test_merge_constructs_correct_path(self, mock_http_client):
        """Constructs correct path: pullrequests/{pull_request_id}/merge."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = PULL_REQUEST_MERGED
        mock_http_client.post = Mock(return_value=mock_response)

        api = PullRequestsAPI(http_client=mock_http_client)

        params = MergePullRequestParams(pull_request_id=42)
        api.merge(params=params)

        call_args = mock_http_client.post.call_args
        assert call_args[1]["path"] == "pullrequests/42/merge"

    def test_merge_serializes_params(self, mock_http_client):
        """Serializes MergePullRequest model to JSON (excluding None values)."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = PULL_REQUEST_MERGED
        mock_http_client.post = Mock(return_value=mock_response)

        api = PullRequestsAPI(http_client=mock_http_client)

        params = MergePullRequestParams(
            pull_request_id=42,
            message="Custom merge message",
            close_source_branch=True,
            merge_strategy="merge_commit",
        )
        api.merge(params=params)

        call_args = mock_http_client.post.call_args
        json_data = call_args[1]["json"]

        assert json_data["message"] == "Custom merge message"
        assert json_data["close_source_branch"] is True

    def test_merge_handles_none_params(self, mock_http_client):
        """Handles params with optional fields omitted."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = PULL_REQUEST_MERGED
        mock_http_client.post = Mock(return_value=mock_response)

        api = PullRequestsAPI(http_client=mock_http_client)
        api.merge(
            params=MergePullRequestParams(
                pull_request_id=42,
                message=None,
                close_source_branch=None,
                merge_strategy="merge_commit",
            )
        )

        call_args = mock_http_client.post.call_args
        json_data = call_args[1]["json"]

        assert json_data.get("merge_strategy") == "merge_commit"

    def test_merge_returns_pull_request_model(self, mock_http_client):
        """Returns merged PullRequest object."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = PULL_REQUEST_MERGED
        mock_http_client.post = Mock(return_value=mock_response)

        api = PullRequestsAPI(http_client=mock_http_client)

        params = MergePullRequestParams(pull_request_id=2)
        result = api.merge(params=params)

        assert isinstance(result, PullRequest)
        assert result.id == 2
        assert result.state == "MERGED"

    def test_merge_handles_api_error(self, mock_http_client):
        """Handles API errors and re-raises BaseClientError."""
        mock_http_client.post = Mock(side_effect=BaseClientError("API error"))

        api = PullRequestsAPI(http_client=mock_http_client)

        params = MergePullRequestParams(pull_request_id=42)

        with pytest.raises(BaseClientError):
            api.merge(params=params)


class TestPullRequestsAPIMergeSimple:
    """Tests for merge_simple() method."""

    @patch.object(PullRequestsAPI, "merge")
    def test_merge_simple_creates_merge_params(self, mock_merge, mock_http_client):
        """Creates MergePullRequest object with close_source_branch parameter."""
        mock_merge.return_value = Mock(spec=PullRequest)

        api = PullRequestsAPI(http_client=mock_http_client)
        api.merge_simple(params=MergePullRequestSimpleParams(pull_request_id=42, close_source_branch=True))

        # Verify merge was called with correct parameters
        mock_merge.assert_called_once()
        call_args = mock_merge.call_args
        params = call_args[0][0]
        assert isinstance(params, MergePullRequestParams)
        assert params.close_source_branch is True

    @patch.object(PullRequestsAPI, "merge")
    def test_merge_simple_default_close_source_branch(self, mock_merge, mock_http_client):
        """Default close_source_branch is False."""
        mock_merge.return_value = Mock(spec=PullRequest)

        api = PullRequestsAPI(http_client=mock_http_client)
        api.merge_simple(params=MergePullRequestSimpleParams(pull_request_id=42))

        call_args = mock_merge.call_args
        params = call_args[0][0]
        assert params.close_source_branch is False

    @patch.object(PullRequestsAPI, "merge")
    def test_merge_simple_returns_merge_result(self, mock_merge, mock_http_client):
        """Returns result from merge()."""
        expected_result = Mock(spec=PullRequest)
        mock_merge.return_value = expected_result

        api = PullRequestsAPI(http_client=mock_http_client)
        result = api.merge_simple(params=MergePullRequestSimpleParams(pull_request_id=42))

        assert result is expected_result


class TestPullRequestsAPIDecline:
    """Tests for decline() method."""

    def test_decline_constructs_correct_path(self, mock_http_client):
        """Constructs correct path: pullrequests/{pull_request_id}/decline."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = PULL_REQUEST_MERGED
        mock_http_client.post = Mock(return_value=mock_response)

        api = PullRequestsAPI(http_client=mock_http_client)
        api.decline(params=DeclinePullRequestParams(pull_request_id=42))

        call_args = mock_http_client.post.call_args
        assert call_args[0][0] == "pullrequests/42/decline"

    def test_decline_returns_pull_request_model(self, mock_http_client):
        """Returns declined PullRequest object."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = PULL_REQUEST_MERGED
        mock_http_client.post = Mock(return_value=mock_response)

        api = PullRequestsAPI(http_client=mock_http_client)
        result = api.decline(params=DeclinePullRequestParams(pull_request_id=3))

        assert isinstance(result, PullRequest)

    def test_decline_handles_api_error(self, mock_http_client):
        """Handles API errors and re-raises BaseClientError."""
        mock_http_client.post = Mock(side_effect=BaseClientError("API error"))

        api = PullRequestsAPI(http_client=mock_http_client)

        with pytest.raises(BaseClientError):
            api.decline(params=DeclinePullRequestParams(pull_request_id=42))
