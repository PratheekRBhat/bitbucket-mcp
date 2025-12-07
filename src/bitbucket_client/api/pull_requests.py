"""
Pull Requests API Module

This module provides classes and methods for interacting with Bitbucket pull requests.
It includes data models for pull request objects and an API client for retrieving
pull request information from the Bitbucket Cloud API.
"""

from typing import List

from bitbucket_client.config import logger
from bitbucket_client.core import BaseClientError, HttpClient
from bitbucket_client.models import (
    CreatePullRequest,
    CreatePullRequestParams,
    DeclinePullRequestParams,
    GetPullRequestParams,
    GetPullRequestsParams,
    MergePullRequest,
    MergePullRequestParams,
    MergePullRequestSimpleParams,
    PullRequest,
    PullRequestBranch,
    PullRequestDestination,
    PullRequestSource,
)


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

    def get(self, params: GetPullRequestParams) -> PullRequest:
        """Retrieve a specific pull request by its ID.

        Fetches detailed information about a single pull request from the Bitbucket API,
        including all associated metadata, participants, and state information.

        Args:
            params: A GetPullRequestParams object containing the pull request ID.

        Returns:
            A PullRequest object containing all pull request details including title,
            description, state, author, source/destination branches, and merge information.

        Raises:
            BaseClientError: If the API request fails or the response cannot be parsed.
        """
        path = f"pullrequests/{params.pull_request_id}"

        try:
            response = self.http_client.get(path=path)

            return PullRequest.model_validate(response.json())

        except BaseClientError as e:
            logger.error("Error getting pull request %d: %s", params.pull_request_id, e)
            raise

    def list(self, params: GetPullRequestsParams) -> List[PullRequest]:
        """List pull requests for the configured repository.

        Retrieves a list of pull requests filtered by state from the Bitbucket API.
        Only returns pull requests for the repository configured in the HTTP client.

        Args:
            params: A GetPullRequestsParams object containing the state of pull requests to retrieve.
                  Valid values are typically "open", "merged", "declined", or "all".

        Returns:
            A list of PullRequest objects matching the specified state filter.
            Each object contains all pull request details including title, description,
            state, author, source/destination branches, and merge information.

        Raises:
            BaseClientError: If the API request fails or the response cannot be parsed.
        """
        try:
            response = self.http_client.get(path="pullrequests", params={"state": params.state.upper()})

            return [PullRequest.model_validate(item) for item in response.json()["values"]]

        except BaseClientError as e:
            logger.error("Error listing pull requests: %s", e)
            raise

    def create(self, params: CreatePullRequestParams) -> PullRequest:
        """Create a new pull request.

        Posts a new pull request to the Bitbucket repository based on the provided
        parameters.

        Args:
            params: A CreatePullRequestParams object containing all the necessary data
                    to create a new pull request, such as title, source, and
                    destination branches, and close source branch.

        Returns:
            A PullRequest object representing the newly created pull request.

        Raises:
            BaseClientError: If the API request fails.
        """
        try:
            json_body = CreatePullRequest(
                title=params.title,
                source=PullRequestSource(branch=PullRequestBranch(name=params.source_branch)),
                destination=PullRequestDestination(branch=PullRequestBranch(name=params.destination_branch)),
                close_source_branch=params.close_source_branch,
            ).model_dump(exclude_none=True)
            response = self.http_client.post("pullrequests", json=json_body)
            return PullRequest.model_validate(response.json())
        except BaseClientError as e:
            logger.error("Error creating pull request: %s", e)
            raise

    def merge(self, params: MergePullRequestParams) -> PullRequest:
        """Merge a pull request.

        Merges a specified pull request using the provided parameters.

        Args:
            params: A MergePullRequestParams object containing the pull request ID and merge options.

        Returns:
            A PullRequest object representing the state of the pull request post-merge.

        Raises:
            BaseClientError: If the API request fails.
        """
        path = f"pullrequests/{params.pull_request_id}/merge"
        try:
            json_body = MergePullRequest(
                message=params.message,
                close_source_branch=params.close_source_branch,
                merge_strategy=params.merge_strategy,
            ).model_dump(exclude_none=True)
            response = self.http_client.post(path=path, json=json_body)
            return PullRequest.model_validate(response.json())
        except BaseClientError as e:
            logger.error("Error merging pull request %d: %s", params.pull_request_id, e)
            raise

    def merge_simple(self, params: MergePullRequestSimpleParams) -> PullRequest:
        """Merge a pull request with default options.

        A simplified version of the merge method that uses default merge options.

        Args:
            params: A MergePullRequestSimpleParams object containing the pull request ID and close source branch.

        Returns:
            A PullRequest object representing the state of the pull request post-merge.

        Raises:
            BaseClientError: If the API request fails.
        """
        return self.merge(
            MergePullRequestParams(
                pull_request_id=params.pull_request_id,
                close_source_branch=params.close_source_branch,
                merge_strategy="merge_commit",
            )
        )

    def decline(self, params: DeclinePullRequestParams) -> PullRequest:
        """Decline a pull request.

        Declines a specified pull request.

        Args:
            params: A DeclinePullRequestParams object containing the pull request ID.

        Returns:
            A PullRequest object representing the state of the pull request post-decline.

        Raises:
            BaseClientError: If the API request fails.
        """
        try:
            response = self.http_client.post(f"pullrequests/{params.pull_request_id}/decline")
            return PullRequest.model_validate(response.json())
        except BaseClientError as e:
            logger.error("Error declining pull request %d: %s", params.pull_request_id, e)
            raise


# TODO: diff of PR, approve, comment crud, update, unapprove, request changes
