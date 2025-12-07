"""Shared pytest fixtures and configuration for bitbucket_client tests."""

import pytest
from unittest.mock import Mock
from httpx import Response


@pytest.fixture
def mock_http_client():
    """Mock HttpClient for testing API methods."""
    client = Mock()
    return client


@pytest.fixture
def mock_pr_response():
    """Mock successful pull request GET response."""
    return {
        "id": 42,
        "title": "Add amazing feature",
        "summary": {"raw": "This PR adds an amazing feature"},
        "state": "OPEN",
        "author": {"display_name": "Pratheek Bhat"},
        "source": {
            "repository": {"type": "repository"},
            "branch": {"name": "feature/amazing"},
            "commit": {"hash": "abc123def456"},
        },
        "destination": {
            "repository": {"type": "repository"},
            "branch": {"name": "main"},
            "commit": {"hash": "def456abc123"},
        },
    }


@pytest.fixture
def mock_pr_list_response(mock_pr_response):
    """Mock paginated PR list response."""
    return {
        "values": [
            mock_pr_response,
            {
                **mock_pr_response,
                "id": 43,
                "title": "Fix critical bug",
                "state": "MERGED",
                "merge_commit": {"hash": "merged123"},
            },
        ]
    }


@pytest.fixture
def mock_create_pr_response():
    """Mock response for creating a new pull request."""
    return {
        "id": 99,
        "title": "New Feature PR",
        "summary": {"raw": "Created via API"},
        "state": "OPEN",
        "author": {"display_name": "API User"},
        "source": {
            "repository": {"type": "repository"},
            "branch": {"name": "feature/new"},
            "commit": {"hash": "new123"},
        },
        "destination": {
            "repository": {"type": "repository"},
            "branch": {"name": "main"},
            "commit": {"hash": "main456"},
        },
    }


@pytest.fixture
def bitbucket_env_vars(monkeypatch):
    """Set up environment variables for testing."""
    monkeypatch.setenv("BITBUCKET_API_TOKEN", "test-token-123")
    return "test-token-123"


@pytest.fixture
def clear_bitbucket_env(monkeypatch):
    """Clear Bitbucket environment variables."""
    monkeypatch.delenv("BITBUCKET_API_TOKEN", raising=False)
