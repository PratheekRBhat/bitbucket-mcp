"""Unit tests for BitbucketClient top-level initialization."""

import pytest
import os
from unittest.mock import patch, Mock

from bitbucket_client.client import BitbucketClient


class TestBitbucketClientInitializationSuccess:
    """Tests for successful BitbucketClient initialization."""

    @patch("bitbucket_client.client.PullRequestsAPI")
    @patch("bitbucket_client.client.HttpClient")
    def test_initializes_with_explicit_token(self, mock_http_client_class, mock_pr_api_class):
        """Client initializes when token is provided explicitly."""
        client = BitbucketClient(
            workspace="my-workspace",
            repo_slug="my-repo",
            token="explicit-token",
        )

        # Verify HttpClient was created with correct parameters
        mock_http_client_class.assert_called_once_with(
            workspace="my-workspace",
            repo_slug="my-repo",
            auth_token="explicit-token",
        )

        # Verify PullRequestsAPI was created
        mock_pr_api_class.assert_called_once()

    @patch("bitbucket_client.client.PullRequestsAPI")
    @patch("bitbucket_client.client.HttpClient")
    def test_initializes_with_env_var_token(self, mock_http_client_class, mock_pr_api_class, bitbucket_env_vars):
        """Client initializes when token is in BITBUCKET_API_TOKEN env var."""
        client = BitbucketClient(
            workspace="my-workspace",
            repo_slug="my-repo",
        )

        # Should use env var token
        mock_http_client_class.assert_called_once_with(
            workspace="my-workspace",
            repo_slug="my-repo",
            auth_token="test-token-123",
        )

    @patch("bitbucket_client.client.PullRequestsAPI")
    @patch("bitbucket_client.client.HttpClient")
    def test_explicit_token_takes_precedence(self, mock_http_client_class, mock_pr_api_class, bitbucket_env_vars):
        """Explicit token takes precedence over environment variable."""
        client = BitbucketClient(
            workspace="my-workspace",
            repo_slug="my-repo",
            token="explicit-wins",
        )

        # Should use explicit token, not env var
        mock_http_client_class.assert_called_once_with(
            workspace="my-workspace",
            repo_slug="my-repo",
            auth_token="explicit-wins",
        )

    @patch("bitbucket_client.client.PullRequestsAPI")
    @patch("bitbucket_client.client.HttpClient")
    def test_pull_requests_api_is_assigned(self, mock_http_client_class, mock_pr_api_class):
        """PullRequestsAPI is instantiated and assigned to self.pull_requests."""
        mock_http_instance = Mock()
        mock_http_client_class.return_value = mock_http_instance
        mock_pr_instance = Mock()
        mock_pr_api_class.return_value = mock_pr_instance

        client = BitbucketClient(
            workspace="my-workspace",
            repo_slug="my-repo",
            token="token",
        )

        assert client.pull_requests is mock_pr_instance
        mock_pr_api_class.assert_called_once_with(http_client=mock_http_instance)


class TestBitbucketClientInitializationFailure:
    """Tests for BitbucketClient initialization failure cases."""

    @patch("bitbucket_client.client.HttpClient")
    def test_raises_error_when_no_token_provided(self, mock_http_client_class, clear_bitbucket_env):
        """Raises ValueError when token is None and env var is not set."""
        with pytest.raises(ValueError) as exc_info:
            BitbucketClient(
                workspace="my-workspace",
                repo_slug="my-repo",
                token=None,
            )

        assert "Bitbucket API token must be provided" in str(exc_info.value)

    @patch("bitbucket_client.client.HttpClient")
    def test_error_message_mentions_env_var(self, mock_http_client_class, clear_bitbucket_env):
        """Error message mentions BITBUCKET_API_TOKEN environment variable."""
        with pytest.raises(ValueError) as exc_info:
            BitbucketClient(workspace="ws", repo_slug="repo")

        assert "BITBUCKET_API_TOKEN" in str(exc_info.value)

    @patch("bitbucket_client.client.HttpClient")
    def test_error_message_mentions_explicit_option(self, mock_http_client_class, clear_bitbucket_env):
        """Error message mentions explicit token option."""
        with pytest.raises(ValueError) as exc_info:
            BitbucketClient(workspace="ws", repo_slug="repo")

        assert "explicitly" in str(exc_info.value)

    @patch("bitbucket_client.client.HttpClient")
    def test_http_client_not_created_when_token_missing(self, mock_http_client_class, clear_bitbucket_env):
        """HttpClient is not instantiated when token validation fails."""
        with pytest.raises(ValueError):
            BitbucketClient(workspace="ws", repo_slug="repo")

        mock_http_client_class.assert_not_called()
