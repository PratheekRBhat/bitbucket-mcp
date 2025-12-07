"""Unit tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from bitbucket_client.models.pull_requests import (
    BranchInfo,
    CommitInfo,
    CreatePullRequest,
    CreatePullRequestReviewer,
    MergeCommit,
    MergePullRequest,
    PullRequest,
    PullRequestAuthor,
    PullRequestBranch,
    PullRequestDestination,
    PullRequestEndpoint,
    PullRequestSource,
    RepositoryInfo,
    Summary,
)


class TestPullRequestModel:
    """Tests for PullRequest model validation."""

    def test_validates_with_all_required_fields(self):
        """Validates correctly with all required fields."""
        data = {
            "id": 1,
            "title": "Test PR",
            "summary": {"raw": "Description"},
            "state": "OPEN",
            "author": {"display_name": "John Doe"},
            "source": {
                "repository": {"type": "repository"},
                "branch": {"name": "feature"},
                "commit": {"hash": "abc123"},
            },
            "destination": {
                "repository": {"type": "repository"},
                "branch": {"name": "main"},
                "commit": {"hash": "def456"},
            },
        }

        pr = PullRequest.model_validate(data)

        assert pr.id == 1
        assert pr.title == "Test PR"
        assert pr.state == "OPEN"

    def test_validates_with_optional_merge_commit(self):
        """Validates with optional merge_commit field."""
        data = {
            "id": 2,
            "title": "Merged PR",
            "summary": {"raw": "Description"},
            "state": "MERGED",
            "merge_commit": {"hash": "merged123"},
            "author": {"display_name": "Jane Doe"},
            "source": {
                "repository": {"type": "repository"},
                "branch": {"name": "feature"},
                "commit": {"hash": "abc123"},
            },
            "destination": {
                "repository": {"type": "repository"},
                "branch": {"name": "main"},
                "commit": {"hash": "def456"},
            },
        }

        pr = PullRequest.model_validate(data)

        assert pr.merge_commit is not None
        assert pr.merge_commit.hash == "merged123"

    def test_validates_with_optional_reason(self):
        """Validates with optional reason field."""
        data = {
            "id": 3,
            "title": "Declined PR",
            "summary": {"raw": "Description"},
            "state": "DECLINED",
            "reason": "Needs more work",
            "author": {"display_name": "Bob Smith"},
            "source": {
                "repository": {"type": "repository"},
                "branch": {"name": "feature"},
                "commit": {"hash": "abc123"},
            },
            "destination": {
                "repository": {"type": "repository"},
                "branch": {"name": "main"},
                "commit": {"hash": "def456"},
            },
        }

        pr = PullRequest.model_validate(data)

        assert pr.reason == "Needs more work"

    def test_fails_validation_when_required_fields_missing(self):
        """Fails validation when required fields are missing."""
        data = {
            "id": 1,
            # missing title
            "summary": {"raw": "Description"},
            "state": "OPEN",
        }

        with pytest.raises(ValidationError):
            PullRequest.model_validate(data)

    def test_nested_models_validate_correctly(self):
        """Correctly parses nested models (author, summary, source, destination)."""
        data = {
            "id": 1,
            "title": "Test PR",
            "summary": {"raw": "Description"},
            "state": "OPEN",
            "author": {"display_name": "John Doe"},
            "source": {
                "repository": {"type": "repository"},
                "branch": {"name": "feature"},
                "commit": {"hash": "abc123"},
            },
            "destination": {
                "repository": {"type": "repository"},
                "branch": {"name": "main"},
                "commit": {"hash": "def456"},
            },
        }

        pr = PullRequest.model_validate(data)

        assert isinstance(pr.author, PullRequestAuthor)
        assert isinstance(pr.summary, Summary)
        assert isinstance(pr.source, PullRequestEndpoint)
        assert isinstance(pr.destination, PullRequestEndpoint)
        assert pr.author.display_name == "John Doe"
        assert pr.summary.raw == "Description"


class TestCreatePullRequestModel:
    """Tests for CreatePullRequest model validation."""

    def test_validates_with_minimum_required_fields(self):
        """Validates with minimum required fields (title, source, destination)."""
        data = {
            "title": "New PR",
            "source": {"branch": {"name": "feature"}},
            "destination": {"branch": {"name": "main"}},
        }

        pr = CreatePullRequest.model_validate(data)

        assert pr.title == "New PR"
        assert pr.source.branch.name == "feature"
        assert pr.destination.branch.name == "main"

    def test_validates_with_all_optional_fields(self):
        """Validates with all optional fields."""
        data = {
            "title": "New PR",
            "source": {"branch": {"name": "feature"}},
            "destination": {"branch": {"name": "main"}},
            "description": "Detailed description",
            "reviewers": [{"uuid": "{user-uuid}", "account_id": "account123"}],
            "close_source_branch": True,
        }

        pr = CreatePullRequest.model_validate(data)

        assert pr.description == "Detailed description"
        assert len(pr.reviewers) == 1
        assert pr.close_source_branch is True

    def test_model_dump_excludes_none_values(self):
        """model_dump(exclude_none=True) excludes None values from output."""
        pr = CreatePullRequest(
            title="New PR",
            source=PullRequestSource(branch=PullRequestBranch(name="feature")),
            destination=PullRequestDestination(branch=PullRequestBranch(name="main")),
            description=None,
        )

        dumped = pr.model_dump(exclude_none=True)

        assert "title" in dumped
        assert "description" not in dumped

    def test_nested_models_validate(self):
        """Nested models (PullRequestSource, PullRequestDestination) validate correctly."""
        data = {
            "title": "New PR",
            "source": {"branch": {"name": "feature/branch"}},
            "destination": {"branch": {"name": "main"}},
        }

        pr = CreatePullRequest.model_validate(data)

        assert isinstance(pr.source, PullRequestSource)
        assert isinstance(pr.destination, PullRequestDestination)
        assert isinstance(pr.source.branch, PullRequestBranch)

    def test_reviewers_list_validates(self):
        """reviewers list validates with correct CreatePullRequestReviewer objects."""
        data = {
            "title": "New PR",
            "source": {"branch": {"name": "feature"}},
            "destination": {"branch": {"name": "main"}},
            "reviewers": [
                {"uuid": "{uuid1}"},
                {"account_id": "account2"},
            ],
        }

        pr = CreatePullRequest.model_validate(data)

        assert len(pr.reviewers) == 2
        assert all(isinstance(r, CreatePullRequestReviewer) for r in pr.reviewers)


class TestMergePullRequestModel:
    """Tests for MergePullRequest model validation."""

    def test_validates_with_all_fields_none(self):
        """Validates with all fields set to None (uses defaults)."""
        pr = MergePullRequest()

        assert pr.message is None
        assert pr.close_source_branch is False
        assert pr.merge_strategy == "merge_commit"

    def test_default_merge_strategy_is_merge_commit(self):
        """Default merge_strategy is 'merge_commit'."""
        pr = MergePullRequest()
        assert pr.merge_strategy == "merge_commit"

    def test_default_close_source_branch_is_false(self):
        """Default close_source_branch is False."""
        pr = MergePullRequest()
        assert pr.close_source_branch is False

    def test_accepts_valid_merge_strategies(self):
        """Accepts valid merge strategies (merge_commit, squash, fast_forward)."""
        for strategy in ["merge_commit", "squash", "fast_forward"]:
            pr = MergePullRequest(merge_strategy=strategy)
            assert pr.merge_strategy == strategy

    def test_model_dump_excludes_none(self):
        """model_dump(exclude_none=True) works correctly."""
        pr = MergePullRequest(
            message=None,
            close_source_branch=True,
        )

        dumped = pr.model_dump(exclude_none=True)

        assert "message" not in dumped
        assert "close_source_branch" in dumped


class TestNestedModels:
    """Tests for nested model validation."""

    def test_pull_request_author_validates(self):
        """PullRequestAuthor validates with display_name."""
        author = PullRequestAuthor(display_name="John Doe")
        assert author.display_name == "John Doe"

    def test_branch_info_validates(self):
        """BranchInfo validates with name."""
        branch = BranchInfo(name="feature/test")
        assert branch.name == "feature/test"

    def test_commit_info_validates(self):
        """CommitInfo validates with hash."""
        commit = CommitInfo(hash="abc123def456")
        assert commit.hash == "abc123def456"

    def test_repository_info_validates(self):
        """RepositoryInfo validates with type."""
        repo = RepositoryInfo(type="repository")
        assert repo.type == "repository"

    def test_pull_request_endpoint_validates(self):
        """PullRequestEndpoint validates with nested repository, branch, and commit."""
        endpoint = PullRequestEndpoint(
            repository=RepositoryInfo(type="repository"),
            branch=BranchInfo(name="main"),
            commit=CommitInfo(hash="abc123"),
        )

        assert endpoint.repository.type == "repository"
        assert endpoint.branch.name == "main"
        assert endpoint.commit.hash == "abc123"

    def test_summary_validates(self):
        """Summary validates with raw text."""
        summary = Summary(raw="This is a description")
        assert summary.raw == "This is a description"

    def test_merge_commit_validates(self):
        """MergeCommit validates with hash."""
        merge_commit = MergeCommit(hash="merged123")
        assert merge_commit.hash == "merged123"
