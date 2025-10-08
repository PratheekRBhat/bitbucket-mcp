"""
Pull Requests API Module

This module provides classes and methods for interacting with Bitbucket pull requests.
It includes data models for pull request objects and an API client for retrieving
pull request information from the Bitbucket Cloud API.
"""

from typing import Optional

from pydantic import BaseModel

from bitbucket_client.core import HttpClient, BaseClientError
from bitbucket_client.config import logger


class PullRequestAuthor(BaseModel):
    """
    Represents the author of a pull request.

    Attributes:
        type (str): The type of author (e.g., 'user').
        display_name (str): The display name of the author.
    """

    type: str
    display_name: str


class PullRequestEndpoint(BaseModel):
    """
    Represents a branch endpoint in a pull request.

    Attributes:
        repository (str): The repository type.
        branch (str): The name of the branch.
        commit_hash (str): The commit hash of the branch.
    """

    repository: str
    branch: str
    commit_hash: str


class PullRequest(BaseModel):
    """
    Represents a Bitbucket pull request.

    Attributes:
        id (int): The unique identifier of the pull request.
        title (str): The title of the pull request.
        summary (str): The summary/description of the pull request.
        state (str): The current state of the pull request (e.g., 'OPEN', 'MERGED', 'DECLINED').
        merge_commit_hash (str): The commit hash of the merge commit.
        reason (Optional[str]): The reason for the current state (optional).
        author (PullRequestAuthor): The author of the pull request.
        source (PullRequestEndpoint): The source branch endpoint.
        destination (PullRequestEndpoint): The destination branch endpoint.
    """

    id: int
    title: str
    summary: str
    state: str
    merge_commit_hash: str
    reason: Optional[str] = ""
    author: PullRequestAuthor
    source: PullRequestEndpoint
    destination: PullRequestEndpoint


class PullRequestsAPI:
    """
    API client for interacting with Bitbucket pull requests.

    Provides methods to retrieve and manipulate pull request data from the Bitbucket API.
    """

    def __init__(self, http_client: HttpClient):
        """
        Initialize the PullRequestsAPI client.

        Args:
            http_client (HttpClient): The HTTP client instance for making API requests.
        """
        self.http_client = http_client

    def _build_response_object(self, response: dict) -> PullRequest:
        """
        Build a PullRequest object from API response data.

        Args:
            response (dict): The raw response dictionary from the Bitbucket API.

        Returns:
            PullRequest: A structured PullRequest object with parsed data.
        """
        author = PullRequestAuthor(
            type=response.get("author").get("type"), display_name=response.get("author").get("display_name")
        )
        source = PullRequestEndpoint(
            repository=response.get("source").get("repository").get("type"),
            branch=response.get("source").get("branch", {}).get("name"),
            commit_hash=response.get("source").get("commit", {}).get("hash"),
        )
        destination = PullRequestEndpoint(
            repository=response.get("destination").get("repository").get("type"),
            branch=response.get("destination").get("branch", {}).get("name"),
            commit_hash=response.get("destination").get("commit", {}).get("hash"),
        )

        return PullRequest(
            id=response.get("id"),
            title=response.get("title"),
            summary=response.get("summary").get("raw"),
            state=response.get("state"),
            merge_commit_hash=response.get("merge_commit").get("hash"),
            reason=response.get("reason") or "",
            author=author,
            source=source,
            destination=destination,
        )

    def get_pull_request(self, pull_request_id: int) -> PullRequest:
        """
        Retrieve a specific pull request by its ID.

        Args:
            pull_request_id (int): The unique identifier of the pull request to retrieve.

        Returns:
            PullRequest: The requested pull request object with full details.

        Raises:
            BaseClientError: If the API request fails or the pull request is not found.
        """
        try:
            response = self.http_client.get(path=self.http_client.base_url, params={"pull_request_id": pull_request_id})
            response = response.json()

            return self._build_response_object(response)
        except BaseClientError as e:
            logger.error("Error getting pull request: %s", e)
            raise e
