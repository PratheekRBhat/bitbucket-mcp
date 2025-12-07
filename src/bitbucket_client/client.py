"""Bitbucket client module.

Provides a high-level wrapper around Bitbucket API for pull request operations.
"""

import os
from typing import Optional

from bitbucket_client.api.pull_requests import PullRequestsAPI
from bitbucket_client.core.http_client import HttpClient


class BitbucketClient:
    """High-level client for interacting with Bitbucket repository.

    Provides access to various API endpoints, currently exposing
    :class:`PullRequestsAPI` via the ``pull_requests`` attribute.
    """

    def __init__(self, workspace: str, repo_slug: str, token: Optional[str] = None):
        """Create a new Bitbucket client.

        Args:
            workspace: The Bitbucket workspace identifier.
            repo_slug: The repository slug within the workspace.
            token: Optional API token. If omitted, the
                ``BITBUCKET_API_TOKEN`` environment variable is used.

        Raises:
            ValueError: If no token is supplied or found in the environment.
        """
        token = os.getenv("BITBUCKET_API_TOKEN") if not token else token
        if not token:
            raise ValueError(
                "Bitbucket API token must be provided explicitly or via the BITBUCKET_API_TOKEN environment variable"
            )

        self._http_client = HttpClient(workspace=workspace, repo_slug=repo_slug, auth_token=token)
        self.pull_requests = PullRequestsAPI(http_client=self._http_client)
