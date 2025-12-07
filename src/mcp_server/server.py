import os
from typing import Optional

from mcp.server.fastmcp import FastMCP

from bitbucket_client import (
    BitbucketClient,
    CreatePullRequest,
    PullRequestSource,
    PullRequestBranch,
    PullRequestDestination,
    MergePullRequest,
)


def init_client():
    """Initialize and return a BitbucketClient instance.

    Reads required configuration from environment variables:
    - BITBUCKET_WORKSPACE: The Bitbucket workspace identifier
    - BITBUCKET_REPO_SLUG: The repository slug within the workspace
    - BITBUCKET_API_TOKEN: The API token for authentication

    Returns:
        BitbucketClient: A configured client instance ready for API operations.

    Raises:
        ValueError: If any required environment variables are not set.
    """
    workspace = os.getenv("BITBUCKET_WORKSPACE")
    repo_slug = os.getenv("BITBUCKET_REPO_SLUG")
    api_token = os.getenv("BITBUCKET_API_TOKEN")

    if not workspace or not repo_slug or not api_token:
        raise ValueError("Missing required environment variables")

    return BitbucketClient(workspace, repo_slug, api_token)


mcp = FastMCP("bitbucket-mcp", json_response=True)


@mcp.tool()
def get_pull_requests(state: str = "open"):
    """List pull requests in the repository.

    Args:
        state: The state of the pull requests to list. Can be 'open', 'merged', or 'declined'.

    Returns:
        A list of pull request objects matching the specified state.
    """
    return init_client().pull_requests.list(state=state)


@mcp.tool()
def get_pull_request(pull_request_id: int):
    """Retrieve a single pull request by its ID.

    Args:
        pull_request_id: The ID of the pull request to retrieve.

    Returns:
        A pull request object with all details for the specified ID.
    """
    return init_client().pull_requests.get(pull_request_id)


@mcp.tool()
def create_pull_request(
    title: str, source_branch: str, destination_branch: str, description: Optional[str] = None, close_source_branch: Optional[bool] = False
):
    """Create a new pull request.

    Args:
        title: The title of the pull request.
        source_branch: The name of the source branch.
        destination_branch: The name of the destination branch.
        description: An optional description for the pull request.
        close_source_branch: Whether to close the source branch after merging.

    Returns:
        A newly created pull request object with the specified parameters.
    """
    return init_client().pull_requests.create(
        CreatePullRequest(
            title=title,
            description=description,
            source=PullRequestSource(branch=PullRequestBranch(name=source_branch)),
            destination=PullRequestDestination(branch=PullRequestBranch(name=destination_branch)),
            close_source_branch=close_source_branch,
        )
    )


@mcp.tool()
def merge_pull_request_simple(pull_request_id: int, close_source_branch: Optional[bool] = False):
    """Merge a pull request using the default merge strategy.

    Args:
        pull_request_id: The ID of the pull request to merge.
        close_source_branch: Whether to close the source branch after merging.

    Returns:
        The merged pull request object.
    """
    return init_client().pull_requests.merge_simple(
        pull_request_id=pull_request_id,
        close_source_branch=close_source_branch,
    )


@mcp.tool()
def merge_pull_request(pull_request_id: int, close_source_branch: Optional[bool] = False, message: Optional[str] = None):
    """Merge a pull request with customizable options.

    Args:
        pull_request_id: The ID of the pull request to merge.
        close_source_branch: Whether to close the source branch after merging.
        message: An optional commit message for the merge.

    Returns:
        The merged pull request object.
    """
    return init_client().pull_requests.merge(
        pull_request_id=pull_request_id,
        params=MergePullRequest(
            close_source_branch=close_source_branch,
            merge_strategy="merge_commit",
            message=message,
        ),
    )


@mcp.tool()
def decline_pull_request(pull_request_id: int):
    """Decline a pull request.

    Args:
        pull_request_id: The ID of the pull request to decline.

    Returns:
        The declined pull request object.
    """
    return init_client().pull_requests.decline(pull_request_id)
