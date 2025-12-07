"""Integration tests for end-to-end API workflows."""

from unittest.mock import patch

import httpx
import pytest
import respx

from bitbucket_client import BitbucketClient
from bitbucket_client.core import BaseClientError
from bitbucket_client.models import (
    CreatePullRequestParams,
    DeclinePullRequestParams,
    GetPullRequestParams,
    GetPullRequestsParams,
    MergePullRequestSimpleParams,
    PullRequest,
)
from tests.fixtures.api_responses import (
    PULL_REQUEST_LIST_RESPONSE,
    PULL_REQUEST_MERGED,
    PULL_REQUEST_OPEN,
)


class TestEndToEndPRWorkflow:
    """End-to-end pull request workflow tests."""

    @respx.mock
    @patch.dict("os.environ", {"BITBUCKET_APP_PASSWORD": "test-token"})
    def test_complete_pr_lifecycle(self):
        """Test complete PR lifecycle: list, get, create, merge."""
        workspace = "test-workspace"
        repo = "test-repo"
        base_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo}/"

        # Mock list PRs
        respx.get(f"{base_url}pullrequests", params={"state": "OPEN"}).mock(
            return_value=httpx.Response(200, json=PULL_REQUEST_LIST_RESPONSE)
        )

        # Mock get specific PR
        respx.get(f"{base_url}pullrequests/1").mock(return_value=httpx.Response(200, json=PULL_REQUEST_OPEN))

        # Mock create PR
        respx.post(f"{base_url}pullrequests").mock(return_value=httpx.Response(201, json=PULL_REQUEST_OPEN))

        # Mock merge PR
        respx.post(f"{base_url}pullrequests/1/merge").mock(return_value=httpx.Response(200, json=PULL_REQUEST_MERGED))

        # Initialize client
        client = BitbucketClient(workspace=workspace, repo_slug=repo)

        # List open PRs
        prs = client.pull_requests.list(params=GetPullRequestsParams(state="open"))
        assert len(prs) == 2
        assert all(isinstance(pr, PullRequest) for pr in prs)

        # Get specific PR
        pr = client.pull_requests.get(params=GetPullRequestParams(pull_request_id=1))
        assert pr.id == 1
        assert pr.title == "Implement user authentication"

        # Create new PR
        new_pr = client.pull_requests.create(
            params=CreatePullRequestParams(
                title="New Feature",
                source_branch="feature",
                destination_branch="main",
            ),
        )
        assert isinstance(new_pr, PullRequest)

        # Merge PR
        merged_pr = client.pull_requests.merge_simple(
            params=MergePullRequestSimpleParams(pull_request_id=1, close_source_branch=False)
        )
        assert merged_pr.state == "MERGED"

    @respx.mock
    @patch.dict("os.environ", {"BITBUCKET_APP_PASSWORD": "test-token"})
    def test_decline_pr_workflow(self):
        """Test declining a pull request."""
        workspace = "test-workspace"
        repo = "test-repo"
        base_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo}/"

        # Mock decline PR
        respx.post(f"{base_url}pullrequests/3/decline").mock(
            return_value=httpx.Response(200, json={**PULL_REQUEST_OPEN, "state": "DECLINED"})
        )

        client = BitbucketClient(workspace=workspace, repo_slug=repo)

        # Decline PR
        declined_pr = client.pull_requests.decline(params=DeclinePullRequestParams(pull_request_id=3))
        assert declined_pr.state == "DECLINED"

    @respx.mock
    @patch.dict("os.environ", {"BITBUCKET_APP_PASSWORD": "test-token"})
    def test_authentication_headers_present(self):
        """Verify all API calls use correct authentication headers."""
        workspace = "test-workspace"
        repo = "test-repo"
        base_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo}/"

        # Mock endpoint that checks headers
        route = respx.get(f"{base_url}pullrequests/1").mock(return_value=httpx.Response(200, json=PULL_REQUEST_OPEN))

        client = BitbucketClient(workspace=workspace, repo_slug=repo)
        client.pull_requests.get(params=GetPullRequestParams(pull_request_id=1))

        # Verify the request was made with correct headers
        assert route.called
        request = route.calls.last.request
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Content-Type"] == "application/json"
        assert request.headers["Accept"] == "application/json"
        assert request.headers["User-Agent"] == "bitbucket-mcp"


class TestErrorHandlingWorkflow:
    """Tests for error handling in API workflows."""

    @respx.mock
    @patch.dict("os.environ", {"BITBUCKET_APP_PASSWORD": "test-token"})
    def test_handles_404_not_found(self):
        """Simulate 404 (not found) and verify error handling."""
        workspace = "test-workspace"
        repo = "test-repo"
        base_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo}/"

        # Mock 404 response
        respx.get(f"{base_url}pullrequests/999").mock(return_value=httpx.Response(404, json={"error": "Not found"}))

        client = BitbucketClient(workspace=workspace, repo_slug=repo)

        # Should raise BaseClientError due to 404
        with pytest.raises(BaseClientError):
            client.pull_requests.get(params=GetPullRequestParams(pull_request_id=999))

    @respx.mock
    @patch.dict("os.environ", {"BITBUCKET_APP_PASSWORD": "test-token"})
    def test_handles_401_unauthorized(self):
        """Simulate 401 (unauthorized) and verify error handling."""
        workspace = "test-workspace"
        repo = "test-repo"
        base_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo}/"

        # Mock 401 response
        respx.get(f"{base_url}pullrequests").mock(return_value=httpx.Response(401, json={"error": "Unauthorized"}))

        client = BitbucketClient(workspace=workspace, repo_slug=repo)

        # Should raise BaseClientError due to 401
        with pytest.raises(BaseClientError):
            client.pull_requests.list(params=GetPullRequestsParams(state="open"))

    @respx.mock
    @patch.dict("os.environ", {"BITBUCKET_APP_PASSWORD": "test-token"})
    def test_handles_500_server_error(self):
        """Simulate 500 (server error) and verify error handling."""
        workspace = "test-workspace"
        repo = "test-repo"
        base_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo}/"

        # Mock 500 response
        respx.post(f"{base_url}pullrequests").mock(
            return_value=httpx.Response(500, json={"error": "Internal server error"})
        )

        client = BitbucketClient(workspace=workspace, repo_slug=repo)

        # Should raise BaseClientError due to 500
        with pytest.raises(BaseClientError):
            client.pull_requests.create(
                params=CreatePullRequestParams(
                    title="New PR",
                    source_branch="feature",
                    destination_branch="main",
                )
            )

    @respx.mock
    @patch.dict("os.environ", {"BITBUCKET_APP_PASSWORD": "test-token"})
    def test_handles_timeout(self):
        """Simulate API timeout and verify error handling."""
        workspace = "test-workspace"
        repo = "test-repo"
        base_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo}/"

        # Mock timeout
        respx.get(f"{base_url}pullrequests/1").mock(side_effect=httpx.TimeoutException("Request timed out"))

        client = BitbucketClient(workspace=workspace, repo_slug=repo)

        # Should raise BaseClientError with timeout info
        with pytest.raises(BaseClientError) as exc_info:
            client.pull_requests.get(params=GetPullRequestParams(pull_request_id=1))

        assert isinstance(exc_info.value.original_exception, httpx.TimeoutException)

    @respx.mock
    @patch.dict("os.environ", {"BITBUCKET_APP_PASSWORD": "test-token"})
    def test_handles_network_error(self):
        """Simulate network error and verify error handling."""
        workspace = "test-workspace"
        repo = "test-repo"
        base_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo}/"

        # Mock network error
        respx.get(f"{base_url}pullrequests").mock(side_effect=httpx.RequestError("Network error"))

        client = BitbucketClient(workspace=workspace, repo_slug=repo)

        # Should raise BaseClientError with network error info
        with pytest.raises(BaseClientError) as exc_info:
            client.pull_requests.list(params=GetPullRequestsParams(state="open"))

        assert isinstance(exc_info.value.original_exception, httpx.RequestError)


class TestAsyncOperations:
    """Tests for async API operations."""

    @pytest.mark.asyncio
    @respx.mock
    @patch.dict("os.environ", {"BITBUCKET_APP_PASSWORD": "test-token"})
    async def test_async_get_pr(self):
        """Test async get PR operation."""
        workspace = "test-workspace"
        repo = "test-repo"
        base_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo}/"

        # Mock async get
        respx.get(f"{base_url}pullrequests/1").mock(return_value=httpx.Response(200, json=PULL_REQUEST_OPEN))

        client = BitbucketClient(workspace=workspace, repo_slug=repo)

        # Use async context manager
        async with client._http_client as http_client:
            response = await http_client.aget(path="pullrequests/1")
            assert response.status_code == 200

    @pytest.mark.asyncio
    @respx.mock
    @patch.dict("os.environ", {"BITBUCKET_APP_PASSWORD": "test-token"})
    async def test_async_error_handling(self):
        """Verify async error handling works correctly."""
        workspace = "test-workspace"
        repo = "test-repo"
        base_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo}/"

        # Mock async timeout
        respx.get(f"{base_url}pullrequests/1").mock(side_effect=httpx.TimeoutException("Async timeout"))

        client = BitbucketClient(workspace=workspace, repo_slug=repo)

        # Should raise BaseClientError for async timeout
        with pytest.raises(BaseClientError) as exc_info:
            async with client._http_client as http_client:
                await http_client.aget(path="pullrequests/1")

        assert isinstance(exc_info.value.original_exception, httpx.TimeoutException)
