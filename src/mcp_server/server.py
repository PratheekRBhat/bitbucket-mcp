import asyncio
import os
import re
from pathlib import Path

import git  # type: ignore[import-untyped]
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from bitbucket_client import BitbucketClient
from bitbucket_client.models import (
    CreatePullRequestParams,
    DeclinePullRequestParams,
    GetPullRequestParams,
    GetPullRequestsParams,
    MergePullRequestParams,
    MergePullRequestSimpleParams,
)

server = Server("bitbucket-mcp")


BITBUCKET_REMOTE_PATTERNS = (
    re.compile(r"git@bitbucket\.org:(?P<workspace>[^/]+)/(?P<repo>[^/]+)(?:\.git)?$"),
    re.compile(r"https?://(?:[^@/]+@)?bitbucket\.org/(?P<workspace>[^/]+)/(?P<repo>[^/]+)(?:\.git)?$"),
)


def _parse_bitbucket_remote(url: str) -> tuple[str, str]:
    """Extract workspace and repo slug from a Bitbucket remote URL."""
    for pattern in BITBUCKET_REMOTE_PATTERNS:
        match = pattern.match(url)
        if match:
            workspace = match.group("workspace")
            repo = match.group("repo")
            if repo.endswith(".git"):
                repo = repo[:-4]
            return workspace, repo
    raise ValueError(f"Unsupported Bitbucket remote URL: {url}")


def init_client():
    """Initialize and return a BitbucketClient instance.

    Discovers the repository context from the local Git configuration and uses
    the BITBUCKET_API_TOKEN environment variable for authentication.

    Returns:
        BitbucketClient: A configured client instance ready for API operations.

    Raises:
        ValueError: If the current directory is not a Git repository, if the
            origin remote is missing, if the remote URL is not a Bitbucket URL,
            or if BITBUCKET_API_TOKEN is not set.
    """
    api_token = os.getenv("BITBUCKET_API_TOKEN")
    if not api_token:
        raise ValueError("Missing BITBUCKET_API_TOKEN environment variable")

    try:
        repo = git.Repo(Path.cwd(), search_parent_directories=True)
    except git.InvalidGitRepositoryError as err:
        raise ValueError("Current directory is not inside a Git repository") from err

    try:
        origin = repo.remote(name="origin")
    except ValueError as err:
        raise ValueError("Git remote 'origin' not found") from err

    workspace, repo_slug = _parse_bitbucket_remote(origin.url)

    return BitbucketClient(workspace, repo_slug, api_token)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Lists all available Bitbucket tools"""
    return [
        Tool(
            name="get_pull_requests",
            description="List pull requests in the repository.",
            inputSchema=GetPullRequestsParams.model_json_schema(),
        ),
        Tool(
            name="get_pull_request",
            description="Retrieve a single pull request by its ID.",
            inputSchema=GetPullRequestParams.model_json_schema(),
        ),
        Tool(
            name="create_pull_request",
            description="Create a new pull request",
            inputSchema=CreatePullRequestParams.model_json_schema(),
        ),
        Tool(
            name="merge_pull_request_simple",
            description="Merge a pull request using the default merge strategy",
            inputSchema=MergePullRequestSimpleParams.model_json_schema(),
        ),
        Tool(
            name="merge_pull_request",
            description="Merge a pull request with customisable options",
            inputSchema=MergePullRequestParams.model_json_schema(),
        ),
        Tool(
            name="decline_pull_request",
            description="Decline a pull request",
            inputSchema=DeclinePullRequestParams.model_json_schema(),
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Calls the appropriate Bitbucket tools based on the provided name"""
    client = init_client()

    match name:
        case "get_pull_requests":
            params = GetPullRequestsParams(**arguments)
            result = client.pull_requests.list(params=params)
        case "get_pull_request":
            params = GetPullRequestParams(**arguments)
            result = client.pull_requests.get(params=params)
        case "create_pull_request":
            params = CreatePullRequestParams(**arguments)
            result = client.pull_requests.create(params=params)
        case "merge_pull_request_simple":
            params = MergePullRequestSimpleParams(**arguments)
            result = client.pull_requests.merge_simple(params=params)
        case "merge_pull_request":
            params = MergePullRequestParams(**arguments)
            result = client.pull_requests.merge(params=params)
        case "decline_pull_request":
            params = DeclinePullRequestParams(**arguments)
            result = client.pull_requests.decline(params=params)
        case _:
            raise ValueError(f"Invalid tool name: {name}")

    return result


async def main():
    """Runs the MCP server using stdio"""
    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)


if __name__ == "__main__":
    asyncio.run(main())
