"""Shared pytest fixtures and configuration for bitbucket_client tests."""

from pathlib import Path
import sys
from unittest.mock import Mock

import pytest
import httpx
from httpx import Response

ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = ROOT / "src"
for path in (ROOT, SRC_PATH):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


@pytest.fixture(autouse=True)
def patch_httpx_clients(monkeypatch):
    original_client = httpx.Client
    original_async_client = httpx.AsyncClient

    def client_factory(*args, **kwargs):
        kwargs.setdefault("verify", False)
        kwargs.setdefault("trust_env", False)
        return original_client(*args, **kwargs)

    def async_client_factory(*args, **kwargs):
        kwargs.setdefault("verify", False)
        kwargs.setdefault("trust_env", False)
        return original_async_client(*args, **kwargs)

    monkeypatch.setattr("bitbucket_client.core.base_client.httpx.Client", client_factory)
    monkeypatch.setattr("bitbucket_client.core.base_client.httpx.AsyncClient", async_client_factory)


@pytest.fixture(autouse=True)
def set_fake_token(monkeypatch):
    monkeypatch.setenv("BITBUCKET_API_TOKEN", "test-token")


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
