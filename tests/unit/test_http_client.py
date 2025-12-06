"""Unit tests for HttpClient Bitbucket-specific configuration."""

import pytest
from unittest.mock import patch, Mock

from bitbucket_client.core.http_client import HttpClient


class TestHttpClientInitialization:
    """Tests for HttpClient initialization."""

    @patch("bitbucket_client.core.http_client.BaseClient.__init__")
    def test_constructs_correct_bitbucket_url(self, mock_base_init):
        """Client constructs correct Bitbucket API base URL from workspace and repo_slug."""
        mock_base_init.return_value = None

        HttpClient(
            workspace="my-workspace",
            repo_slug="my-repo",
            auth_password="secret123",
        )

        # Verify BaseClient.__init__ was called with correct base_url
        call_args = mock_base_init.call_args
        expected_url = "https://api.bitbucket.org/2.0/repositories/my-workspace/my-repo/"
        assert call_args[1]["base_url"] == expected_url

    @patch("bitbucket_client.core.http_client.BaseClient.__init__")
    def test_sets_authorization_bearer_header(self, mock_base_init):
        """Authorization header is set with Bearer token format."""
        mock_base_init.return_value = None

        HttpClient(
            workspace="test-ws",
            repo_slug="test-repo",
            auth_password="my-token",
        )

        call_args = mock_base_init.call_args
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer my-token"

    @patch("bitbucket_client.core.http_client.BaseClient.__init__")
    def test_sets_content_type_header(self, mock_base_init):
        """Content-Type header is set to application/json."""
        mock_base_init.return_value = None

        HttpClient(
            workspace="test-ws",
            repo_slug="test-repo",
            auth_password="token",
        )

        call_args = mock_base_init.call_args
        headers = call_args[1]["headers"]
        assert headers["Content-Type"] == "application/json"

    @patch("bitbucket_client.core.http_client.BaseClient.__init__")
    def test_sets_accept_header(self, mock_base_init):
        """Accept header is set to application/json."""
        mock_base_init.return_value = None

        HttpClient(
            workspace="test-ws",
            repo_slug="test-repo",
            auth_password="token",
        )

        call_args = mock_base_init.call_args
        headers = call_args[1]["headers"]
        assert headers["Accept"] == "application/json"

    @patch("bitbucket_client.core.http_client.BaseClient.__init__")
    def test_sets_user_agent_header(self, mock_base_init):
        """User-Agent header is set to bitbucket-mcp."""
        mock_base_init.return_value = None

        HttpClient(
            workspace="test-ws",
            repo_slug="test-repo",
            auth_password="token",
        )

        call_args = mock_base_init.call_args
        headers = call_args[1]["headers"]
        assert headers["User-Agent"] == "bitbucket-mcp"

    @patch("bitbucket_client.core.http_client.BaseClient.__init__")
    def test_all_headers_correctly_set(self, mock_base_init):
        """All required headers are present and correct."""
        mock_base_init.return_value = None

        HttpClient(
            workspace="workspace1",
            repo_slug="repo1",
            auth_password="password123",
        )

        call_args = mock_base_init.call_args
        headers = call_args[1]["headers"]

        expected_headers = {
            "Authorization": "Bearer password123",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "bitbucket-mcp",
        }

        assert headers == expected_headers


class TestHttpClientURLConstruction:
    """Tests for URL construction patterns."""

    @patch("bitbucket_client.core.http_client.BaseClient.__init__")
    def test_url_pattern_with_different_workspaces(self, mock_base_init):
        """Base URL correctly uses different workspace names."""
        mock_base_init.return_value = None

        HttpClient(workspace="acme-corp", repo_slug="api", auth_password="token")
        url1 = mock_base_init.call_args[1]["base_url"]

        HttpClient(workspace="different-workspace", repo_slug="api", auth_password="token")
        url2 = mock_base_init.call_args[1]["base_url"]

        assert "acme-corp" in url1
        assert "different-workspace" in url2
        assert url1 != url2

    @patch("bitbucket_client.core.http_client.BaseClient.__init__")
    def test_url_pattern_with_different_repos(self, mock_base_init):
        """Base URL correctly uses different repo slugs."""
        mock_base_init.return_value = None

        HttpClient(workspace="workspace", repo_slug="backend-api", auth_password="token")
        url1 = mock_base_init.call_args[1]["base_url"]

        HttpClient(workspace="workspace", repo_slug="frontend", auth_password="token")
        url2 = mock_base_init.call_args[1]["base_url"]

        assert "backend-api" in url1
        assert "frontend" in url2
        assert url1 != url2

    @patch("bitbucket_client.core.http_client.BaseClient.__init__")
    def test_url_has_trailing_slash(self, mock_base_init):
        """Base URL ends with a trailing slash."""
        mock_base_init.return_value = None

        HttpClient(workspace="ws", repo_slug="repo", auth_password="token")

        call_args = mock_base_init.call_args
        url = call_args[1]["base_url"]
        assert url.endswith("/")
