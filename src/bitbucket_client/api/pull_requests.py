"""
Pull Requests API Module

This module provides classes and methods for interacting with Bitbucket pull requests.
It includes data models for pull request objects and an API client for retrieving
pull request information from the Bitbucket Cloud API.
"""

from typing import List, Optional

from bitbucket_client.config import logger
from bitbucket_client.core import BaseClientError, HttpClient
from bitbucket_client.models import PullRequest, CreatePullRequest, MergePullRequest


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

    def create(self, params: CreatePullRequest) -> PullRequest:
        """Create a new pull request.

        Posts a new pull request to the Bitbucket repository based on the provided
        parameters.

        Args:
            params: A CreatePullRequest object containing all the necessary data
                    to create a new pull request, such as title, source, and
                    destination branches.

        Returns:
            A PullRequest object representing the newly created pull request.

        Raises:
            BaseClientError: If the API request fails.
        """
        try:
            response = self.http_client.post("pullrequests", json=params.model_dump(exclude_none=True))
            return PullRequest.model_validate(response.json())
        except BaseClientError as e:
            logger.error("Error creating pull request: %s", e)
            raise

    def merge(self, pull_request_id: int, params: Optional[MergePullRequest]) -> PullRequest:
        """Merge a pull request.

        Merges a specified pull request using the provided parameters.

        Args:
            pull_request_id: The ID of the pull request to merge.
            params: An optional MergePullRequest object with merge options like
                    commit message, branch closing, and merge strategy.

        Returns:
            A PullRequest object representing the state of the pull request post-merge.

        Raises:
            BaseClientError: If the API request fails.
        """
        path = f"pullrequests/{pull_request_id}/merge"
        try:
            json_body = params.model_dump(exclude_none=True) if params else {}
            response = self.http_client.post(path=path, json=json_body)
            return PullRequest.model_validate(response.json())
        except BaseClientError as e:
            logger.error("Error merging pull request %d: %s", pull_request_id, e)
            raise

    def merge_simple(self, pull_request_id: int, close_source_branch: bool = False) -> PullRequest:
        """Merge a pull request with default options.

        A simplified version of the merge method that uses default merge options.

        Args:
            pull_request_id: The ID of the pull request to merge.
            close_source_branch: If True, the source branch will be deleted after merging.
                                 Defaults to False.

        Returns:
            A PullRequest object representing the state of the pull request post-merge.

        Raises:
            BaseClientError: If the API request fails.
        """
        params = MergePullRequest(close_source_branch=close_source_branch)
        return self.merge(pull_request_id, params)

    def decline(self, pull_request_id: int) -> PullRequest:
        """Decline a pull request.

        Declines a specified pull request.

        Args:
            pull_request_id: The ID of the pull request to decline.

        Returns:
            A PullRequest object representing the state of the pull request post-decline.

        Raises:
            BaseClientError: If the API request fails.
        """
        try:
            response = self.http_client.post(f"pullrequests/{pull_request_id}/decline")
            return PullRequest.model_validate(response.json())
        except BaseClientError as e:
            logger.error("Error declining pull request %d: %s", pull_request_id, e)
            raise

#TODO: diff of PR, approve, comment crud, update, unapprove, request changes