"""
Pull Requests API Module

This module provides classes and methods for interacting with Bitbucket pull requests.
It includes data models for pull request objects and an API client for retrieving
pull request information from the Bitbucket Cloud API.
"""

from typing import Optional, List

from pydantic import BaseModel

from bitbucket_client.config import logger
from bitbucket_client.core import BaseClientError, HttpClient

# --- Pydantic Models ---


class PullRequestAuthor(BaseModel):
    """Represents the author information of a pull request.

    Contains basic user information for the person who created the pull request.
    """

    display_name: str


class BranchInfo(BaseModel):
    """Represents branch information in a pull request context.

    Contains the name of a Git branch involved in a pull request operation.
    """

    name: str


class CommitInfo(BaseModel):
    """Represents commit information in a pull request context.

    Contains the hash identifier of a Git commit involved in a pull request.
    """

    hash: str


class RepositoryInfo(BaseModel):
    """Represents repository information in a pull request context.

    Contains metadata about the repository involved in a pull request operation.
    """

    type: str


class PullRequestEndpoint(BaseModel):
    """Represents an endpoint (source or destination) of a pull request.

    Contains information about the repository, branch, and commit that form
    either the source or destination of a pull request operation.
    """

    repository: RepositoryInfo
    branch: BranchInfo
    commit: CommitInfo


class Summary(BaseModel):
    """Represents the summary/description content of a pull request.

    Contains the raw text content of the pull request description or summary.
    """

    raw: str


class MergeCommit(BaseModel):
    """Represents the merge commit information of a pull request.

    Contains the hash of the commit that resulted from merging the pull request,
    if the pull request has been merged.
    """

    hash: str


class PullRequest(BaseModel):
    """Represents a complete Bitbucket pull request with all associated data.

    This is the main model that contains all information about a pull request,
    including its metadata, content, state, participants, and endpoints.
    """

    id: int
    title: str
    summary: Summary
    state: str
    merge_commit: Optional[MergeCommit] = None
    reason: Optional[str] = ""
    author: PullRequestAuthor
    source: PullRequestEndpoint
    destination: PullRequestEndpoint


# --- API Class ---


class PullRequestsAPI:
    """API client for interacting with Bitbucket pull requests.

    Provides methods to retrieve and manipulate pull request data from the Bitbucket Cloud API.
    This client handles authentication, request formatting, and response parsing for pull request
    operations.

    Args:
        http_client: An instance of HttpClient configured for Bitbucket API communication.
    """

    def __init__(self, http_client: HttpClient):
        self.http_client = http_client

    def get(self, pull_request_id: int) -> PullRequest:
        """Retrieve a specific pull request by its ID.

        Fetches detailed information about a single pull request from the Bitbucket API,
        including all associated metadata, participants, and state information.

        Args:
            pull_request_id: The unique numeric identifier of the pull request to retrieve.

        Returns:
            A PullRequest object containing all pull request details including title,
            description, state, author, source/destination branches, and merge information.

        Raises:
            BaseClientError: If the API request fails or the response cannot be parsed.
        """
        path = f"pullrequests/{pull_request_id}"

        try:
            response = self.http_client.get(path=path)

            return PullRequest.model_validate(response.json())

        except BaseClientError as e:
            logger.error("Error getting pull request %d: %s", pull_request_id, e)
            raise

    def list(self, state: str = "open") -> List[PullRequest]:
        """List pull requests for the configured repository.

        Retrieves a list of pull requests filtered by state from the Bitbucket API.
        Only returns pull requests for the repository configured in the HTTP client.

        Args:
            state: The state of pull requests to retrieve. Defaults to "open".
                  Valid values are typically "open", "merged", "declined", or "all".

        Returns:
            A list of PullRequest objects matching the specified state filter.
            Each object contains all pull request details including title, description,
            state, author, source/destination branches, and merge information.

        Raises:
            BaseClientError: If the API request fails or the response cannot be parsed.
        """
        try:
            response = self.http_client.get(path="pullrequests", params={"state": state.upper()})

            return [PullRequest.model_validate(item) for item in response.json()["values"]]

        except BaseClientError as e:
            logger.error("Error listing pull requests: %s", e)
            raise
