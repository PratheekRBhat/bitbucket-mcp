"""Unit tests for BitbucketClient top-level initialization."""

import pytest
import os
from unittest.mock import patch, Mock

from bitbucket_client.client import BitbucketClient


class TestBitbucketClientInitializationSuccess:
    """Tests for successful BitbucketClient initialization."""

    @patch("bitbucket_client.client.PullRequestsAPI")
    @patch("bitbucket_client.client.HttpClient")
    def test_initializes_with_explicit_password(self, mock_http_client_class, mock_pr_api_class):
        """Client initializes when password is provided explicitly."""
        client = BitbucketClient(
            workspace="my-workspace",
            repo_slug="my-repo",
            password="explicit-password",
        )

        # Verify HttpClient was created with correct parameters
        mock_http_client_class.assert_called_once_with(
            workspace="my-workspace",
            repo_slug="my-repo",
            auth_password="explicit-password",
        )

        # Verify PullRequestsAPI was created
        mock_pr_api_class.assert_called_once()

    @patch("bitbucket_client.client.PullRequestsAPI")
    @patch("bitbucket_client.client.HttpClient")
    def test_initializes_with_env_var_password(self, mock_http_client_class, mock_pr_api_class, bitbucket_env_vars):
        """Client initializes when password is in BITBUCKET_APP_PASSWORD env var."""
        client = BitbucketClient(
            workspace="my-workspace",
            repo_slug="my-repo",
        )

        # Should use env var password
        mock_http_client_class.assert_called_once_with(
            workspace="my-workspace",
            repo_slug="my-repo",
            auth_password="test-password-123",
        )

    @patch("bitbucket_client.client.PullRequestsAPI")
    @patch("bitbucket_client.client.HttpClient")
    def test_explicit_password_takes_precedence(self, mock_http_client_class, mock_pr_api_class, bitbucket_env_vars):
        """Explicit password takes precedence over environment variable."""
        client = BitbucketClient(
            workspace="my-workspace",
            repo_slug="my-repo",
            password="explicit-wins",
        )

        # Should use explicit password, not env var
        mock_http_client_class.assert_called_once_with(
            workspace="my-workspace",
            repo_slug="my-repo",
            auth_password="explicit-wins",
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
            password="password",
        )

        assert client.pull_requests is mock_pr_instance
        mock_pr_api_class.assert_called_once_with(http_client=mock_http_instance)


class TestBitbucketClientInitializationFailure:
    """Tests for BitbucketClient initialization failure cases."""

    @patch("bitbucket_client.client.HttpClient")
    def test_raises_error_when_no_password_provided(self, mock_http_client_class, clear_bitbucket_env):
        """Raises ValueError when password is None and env var is not set."""
        with pytest.raises(ValueError) as exc_info:
            BitbucketClient(
                workspace="my-workspace",
                repo_slug="my-repo",
                password=None,
            )

        assert "Bitbucket app password must be provided" in str(exc_info.value)

    @patch("bitbucket_client.client.HttpClient")
    def test_error_message_mentions_env_var(self, mock_http_client_class, clear_bitbucket_env):
        """Error message mentions BITBUCKET_APP_PASSWORD environment variable."""
        with pytest.raises(ValueError) as exc_info:
            BitbucketClient(workspace="ws", repo_slug="repo")

        assert "BITBUCKET_APP_PASSWORD" in str(exc_info.value)

    @patch("bitbucket_client.client.HttpClient")
    def test_error_message_mentions_explicit_option(self, mock_http_client_class, clear_bitbucket_env):
        """Error message mentions explicit password option."""
        with pytest.raises(ValueError) as exc_info:
            BitbucketClient(workspace="ws", repo_slug="repo")

        assert "explicitly" in str(exc_info.value)

    @patch("bitbucket_client.client.HttpClient")
    def test_http_client_not_created_when_password_missing(self, mock_http_client_class, clear_bitbucket_env):
        """HttpClient is not instantiated when password validation fails."""
        with pytest.raises(ValueError):
            BitbucketClient(workspace="ws", repo_slug="repo")

        mock_http_client_class.assert_not_called()
