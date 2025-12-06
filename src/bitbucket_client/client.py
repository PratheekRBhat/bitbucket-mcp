"""Bitbucket client module.

Provides a high-level wrapper around Bitbucket API for pull request operations.
"""
import os
from typing import Optional

from bitbucket_client.core.http_client import HttpClient
from bitbucket_client.api.pull_requests import PullRequestsAPI


class BitbucketClient:
    """High-level client for interacting with Bitbucket repository.

    Provides access to various API endpoints, currently exposing
    :class:`PullRequestsAPI` via the ``pull_requests`` attribute.
    """

    def __init__(self, workspace: str, repo_slug: str, password: Optional[str] = None):
        """Create a new Bitbucket client.

        Args:
            workspace: The Bitbucket workspace identifier.
            repo_slug: The repository slug within the workspace.
            password: Optional app password. If omitted, the
                ``BITBUCKET_APP_PASSWORD`` environment variable is used.

        Raises:
            ValueError: If no password is supplied or found in the environment.
        """
        password = os.getenv("BITBUCKET_APP_PASSWORD") if not password else password
        if not password:
            raise ValueError(
                "Bitbucket app password must be provided explicitly or via the BITBUCKET_APP_PASSWORD environment variable"
            )

        self._http_client = HttpClient(workspace=workspace, repo_slug=repo_slug, auth_password=password)
        self.pull_requests = PullRequestsAPI(http_client=self._http_client)
