"""
Data models for Bitbucket pull requests.

This module defines Pydantic models that represent the structure of pull request
data as returned by the Bitbucket API. These models are used for type hinting
and data validation throughout the client.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class PullRequestAuthor(BaseModel):
    """
    Represents the author of a pull request.

    Attributes:
        display_name: The author's display name.
    """

    display_name: str


class BranchInfo(BaseModel):
    """
    Represents a Git branch.

    Attributes:
        name: The name of the branch.
    """

    name: str


class CommitInfo(BaseModel):
    """
    Represents a Git commit.

    Attributes:
        hash: The commit hash.
    """

    hash: str


class RepositoryInfo(BaseModel):
    """
    Represents a Bitbucket repository.

    Attributes:
        type: The type of the repository (e.g., "repository").
    """

    type: str


class PullRequestEndpoint(BaseModel):
    """
    Represents the source or destination of a pull request.

    This model encapsulates the repository, branch, and commit information for
    either the source or the destination of a pull request.

    Attributes:
        repository: The repository information.
        branch: The branch information.
        commit: The commit information.
    """

    repository: RepositoryInfo
    branch: BranchInfo
    commit: CommitInfo


class Summary(BaseModel):
    """
    Represents the summary (description) of a pull request.

    Attributes:
        raw: The raw, unformatted text of the pull request's description.
    """

    raw: str


class MergeCommit(BaseModel):
    """
    Represents the merge commit of a pull request.

    This model is present when a pull request has been merged.

    Attributes:
        hash: The hash of the merge commit.
    """

    hash: str


class PullRequest(BaseModel):
    """
    Represents a Bitbucket pull request.

    This is the main data model for a pull request, containing all relevant
    details such as its ID, title, state, author, and endpoints.

    Attributes:
        id: The unique identifier for the pull request.
        title: The title of the pull request.
        summary: The summary or description of the pull request.
        state: The current state of the pull request (e.g., "OPEN", "MERGED").
        merge_commit: The merge commit information, if the PR is merged.
        reason: The reason for the pull request's current state (e.g., if declined).
        author: The author of the pull request.
        source: The source endpoint of the pull request.
        destination: The destination endpoint of the pull request.
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


class PullRequestBranch(BaseModel):
    """Specifies a branch for a pull request source or destination.

    Attributes:
        name: The name of the branch (e.g., 'feature/new-thing').
    """

    name: str = Field(..., description="Name of the branch (e.g., 'feature/new-thing')")


class PullRequestSource(BaseModel):
    """The source of a pull request to be created.

    Attributes:
        branch: The source branch from which the code is being pulled.
    """

    branch: PullRequestBranch = Field(..., description="The source branch for the pull request.")


class PullRequestDestination(BaseModel):
    """The destination of a pull request to be created.

    Attributes:
        branch: The destination branch into which the code will be merged.
    """

    branch: PullRequestBranch = Field(..., description="The destination branch for the pull request.")


class CreatePullRequestReviewer(BaseModel):
    """Specifies a reviewer for a new pull request.

    Attributes:
        uuid: The UUID of the reviewer (e.g., '{account-uuid}').
        account_id: The Atlassian Account ID (AAID) of the reviewer.
    """

    uuid: Optional[str] = Field(None, description="The UUID of the reviewer (e.g., '{account-uuid}')")
    account_id: Optional[str] = Field(None, description="The Atlassian Account ID (AAID) of the reviewer.")


class CreatePullRequest(BaseModel):
    """Data model for creating a new Bitbucket pull request.

    This model represents the JSON payload required by the Bitbucket API
    to create a new pull request.

    Attributes:
        title: The title of the pull request.
        source: The source branch and repository for the pull request.
        destination: The destination branch and repository for the pull request.
        description: The description of the pull request (supports Markdown).
        reviewers: A list of reviewers to be added to the pull request.
        close_source_branch: If true, the source branch will be deleted upon merge.
    """

    title: str = Field(..., description="The title of the pull request.")
    source: PullRequestSource = Field(..., description="The source branch for the pull request.")
    destination: PullRequestDestination = Field(..., description="The destination branch for the pull request.")
    description: Optional[str] = Field(
        None, description="A detailed description of the pull request (supports Markdown)."
    )
    reviewers: Optional[List[CreatePullRequestReviewer]] = Field(
        None, description="A list of users to review the pull request."
    )
    close_source_branch: bool = Field(
        False, description="Whether to close the source branch after the pull request is merged."
    )


class MergePullRequest(BaseModel):
    """Data model for merging a pull request.

    Represents the JSON payload for a pull request merge operation.

    Attributes:
        message: Optional custom message for the merge commit.
        close_source_branch: If True, deletes the source branch after merging.
                             Defaults to False.
        merge_strategy: The merge strategy to use. Can be 'merge_commit',
                        'squash', or 'fast_forward'. Defaults to 'merge_commit'.
    """

    message: Optional[str] = Field(None, description="Custom message for the merge commit")
    close_source_branch: Optional[bool] = Field(False, description="Whether to delete the source branch after merging.")
    merge_strategy: Optional[str] = Field(
        "merge_commit", description="Merge strategy: 'merge_commit', 'squash', or 'fast_forward'."
    )


class GetPullRequestsParams(BaseModel):
    """Parameters for listing pull requests."""

    state: Literal["open", "merged", "declined"] = Field(..., description="The state of the pull requests to list.")


class GetPullRequestParams(BaseModel):
    """Parameters for retrieving a single pull request."""

    pull_request_id: int = Field(..., description="The unique identifier of the pull request.")


class CreatePullRequestParams(BaseModel):
    """Parameters for creating a new pull request."""

    title: str = Field(..., description="The title of the new pull request.")
    description: Optional[str] = Field(default="", description="A detailed description of the pull request's changes.")
    source_branch: str = Field(..., description="The name of the branch where the changes are implemented.")
    destination_branch: str = Field(..., description="The name of the branch the changes will be merged into.")
    close_source_branch: Optional[bool] = Field(
        default=False, description="If true, the source branch will be deleted after the pull request is merged."
    )


class MergePullRequestSimpleParams(BaseModel):
    """Parameters for a simple pull request merge."""

    pull_request_id: int = Field(..., description="The unique identifier of the pull request to merge.")
    close_source_branch: Optional[bool] = Field(
        default=False, description="If true, the source branch will be deleted after the pull request is merged."
    )


class MergePullRequestParams(BaseModel):
    """Parameters for merging a pull request with advanced options."""

    pull_request_id: int = Field(..., description="The unique identifier of the pull request to merge.")
    merge_strategy: Literal["merge_commit", "squash", "fast_forward"] = Field(
        default="merge_commit", description="The merge strategy to use."
    )
    message: Optional[str] = Field(default="", description="An optional custom message for the merge commit.")
    close_source_branch: Optional[bool] = Field(
        default=False, description="If true, the source branch will be deleted after the pull request is merged."
    )


class DeclinePullRequestParams(BaseModel):
    """Parameters for declining a pull request."""

    pull_request_id: int = Field(..., description="The unique identifier of the pull request to decline.")
