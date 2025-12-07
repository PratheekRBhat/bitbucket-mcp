# Bitbucket MCP Client

A Python-based client to interact with the Bitbucket Cloud API, allowing you to manage pull requests programmatically.

## Installation

```bash
pip install bitbucket-mcp
```

## Configuration

You need a Bitbucket API Token with the appropriate permissions (Repositories: Read/Write, Pull Requests: Read/Write). You can create one in your Atlassian account settings.

Set it as an environment variable:

```bash
export BITBUCKET_API_TOKEN="your-api-token"
```

The workspace and repository slug are now discovered automatically from the local Git repository’s `origin` remote. No additional configuration is required.

## Usage

### Initialization

```python
from bitbucket_client import BitbucketClient

# Initialize with your workspace and repository slug
# Token is read from BITBUCKET_API_TOKEN env var by default
client = BitbucketClient(
    workspace="your-workspace",
    repo_slug="your-repo-slug"
)
```

### List Pull Requests

```python
# List all open pull requests
open_prs = client.pull_requests.list(state="open")

for pr in open_prs:
    print(f"#{pr.id}: {pr.title} ({pr.author.display_name})")
```

### Get a Pull Request

```python
pr = client.pull_requests.get(pull_request_id=123)
print(f"Title: {pr.title}")
print(f"Description: {pr.summary.raw}")
```

### Create a Pull Request

```python
from bitbucket_client.models import CreatePullRequest, PullRequestSource, PullRequestDestination, PullRequestBranch

new_pr = client.pull_requests.create(
    CreatePullRequest(
        title="My New Feature",
        description="Implements the new feature X",
        source=PullRequestSource(branch=PullRequestBranch(name="feature/new-feature")),
        destination=PullRequestDestination(branch=PullRequestBranch(name="main")),
        close_source_branch=True
    )
)
print(f"Created PR #{new_pr.id}")
```

### Merge a Pull Request

```python
# Simple merge
client.pull_requests.merge_simple(pull_request_id=123, close_source_branch=True)

# Or with more options
from bitbucket_client.models import MergePullRequest

client.pull_requests.merge(
    pull_request_id=123,
    params=MergePullRequest(
        message="Merging feature X",
        merge_strategy="squash",
        close_source_branch=True
    )
)
```

### Decline a Pull Request

```python
client.pull_requests.decline(pull_request_id=123)
```

## Error Handling

```python
from bitbucket_client import BaseClientError

try:
    client.pull_requests.get(99999)
except BaseClientError as e:
    print(f"API Error: {e}")
```
