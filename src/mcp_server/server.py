import os
import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

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
