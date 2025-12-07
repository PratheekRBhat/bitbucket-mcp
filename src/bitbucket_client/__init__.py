"""
Bitbucket MCP Client Package

A Python-based client to interact with the Bitbucket Cloud API for managing pull requests.
"""

__version__ = "0.1.0"

from .client import BitbucketClient
from .exceptions import BaseClientError
from .models import PullRequest, CreatePullRequest, MergePullRequest, PullRequestSource, PullRequestDestination, PullRequestBranch

__all__ = ["BitbucketClient", "BaseClientError", "PullRequest", "CreatePullRequest", "MergePullRequest", "PullRequestSource", "PullRequestDestination", "PullRequestBranch"]
