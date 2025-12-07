"""Tests for the MCP server layer."""

from contextlib import asynccontextmanager
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from mcp_server import server

API_TOKEN = "test-token"


class FakeRemote:
    def __init__(self, url: str):
        self.url = url


class FakeRepo:
    def __init__(self, url: str):
        self._remote = FakeRemote(url)

    def remote(self, name: str):
        if name != "origin":
            raise ValueError("remote not found")
        return self._remote


class FakePullRequests:
    def __init__(self):
        self.calls: list[tuple[str, object]] = []

    def _record(self, name: str, params: object, result: object):
        self.calls.append((name, params))
        return result

    def list(self, params):
        return self._record("list", params, "list-result")

    def get(self, params):
        return self._record("get", params, "get-result")

    def create(self, params):
        return self._record("create", params, "create-result")

    def merge_simple(self, params):
        return self._record("merge_simple", params, "merge_simple-result")

    def merge(self, params):
        return self._record("merge", params, "merge-result")

    def decline(self, params):
        return self._record("decline", params, "decline-result")


class FakeClient:
    def __init__(self):
        self.pull_requests = FakePullRequests()


@pytest.fixture
def patched_token(monkeypatch):
    monkeypatch.setenv("BITBUCKET_API_TOKEN", API_TOKEN)


def test_init_client_uses_git_https(monkeypatch, patched_token):
    captured = {}

    class StubClient:
        def __init__(self, workspace, repo_slug, token):
            captured["workspace"] = workspace
            captured["repo_slug"] = repo_slug
            captured["token"] = token

    monkeypatch.setattr(server, "BitbucketClient", StubClient)
    monkeypatch.setattr(server.git, "Repo", lambda path, search_parent_directories: FakeRepo("https://bitbucket.org/ws/repo.git"))

    result = server.init_client()

    assert isinstance(result, StubClient)
    assert captured == {"workspace": "ws", "repo_slug": "repo", "token": API_TOKEN}


def test_init_client_uses_git_ssh(monkeypatch, patched_token):
    captured = {}

    class StubClient:
        def __init__(self, workspace, repo_slug, token):
            captured["workspace"] = workspace
            captured["repo_slug"] = repo_slug
            captured["token"] = token

    monkeypatch.setattr(server, "BitbucketClient", StubClient)
    monkeypatch.setattr(server.git, "Repo", lambda path, search_parent_directories: FakeRepo("git@bitbucket.org:ws/repo.git"))

    result = server.init_client()

    assert isinstance(result, StubClient)
    assert captured == {"workspace": "ws", "repo_slug": "repo", "token": API_TOKEN}


def test_init_client_missing_origin(monkeypatch, patched_token):
    class NoOriginRepo:
        def remote(self, name: str):
            raise ValueError("not found")

    monkeypatch.setattr(server, "BitbucketClient", lambda w, r, t: None)
    monkeypatch.setattr(server.git, "Repo", lambda path, search_parent_directories: NoOriginRepo())

    with pytest.raises(ValueError):
        server.init_client()


def test_init_client_invalid_repo(monkeypatch, patched_token):
    monkeypatch.setattr(server, "BitbucketClient", lambda w, r, t: None)

    class DummyError(server.git.InvalidGitRepositoryError):
        pass

    def raise_invalid(*args, **kwargs):
        raise DummyError()

    monkeypatch.setattr(server.git, "Repo", raise_invalid)

    with pytest.raises(ValueError):
        server.init_client()


def test_init_client_invalid_remote(monkeypatch, patched_token):
    monkeypatch.setattr(server, "BitbucketClient", lambda w, r, t: None)
    monkeypatch.setattr(server.git, "Repo", lambda path, search_parent_directories: FakeRepo("https://example.com/foo/bar.git"))

    with pytest.raises(ValueError):
        server.init_client()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tool_name", "arguments", "expected_call"),
    [
        ("get_pull_requests", {"state": "open"}, ("list", server.GetPullRequestsParams(state="open"))),
        ("get_pull_request", {"pull_request_id": 1}, ("get", server.GetPullRequestParams(pull_request_id=1))),
        (
            "create_pull_request",
            {"title": "t", "source_branch": "src", "destination_branch": "dest", "description": "d"},
            (
                "create",
                server.CreatePullRequestParams(
                    title="t", source_branch="src", destination_branch="dest", description="d", close_source_branch=False
                ),
            ),
        ),
        (
            "merge_pull_request_simple",
            {"pull_request_id": 2, "close_source_branch": True},
            ("merge_simple", server.MergePullRequestSimpleParams(pull_request_id=2, close_source_branch=True)),
        ),
        (
            "merge_pull_request",
            {
                "pull_request_id": 3,
                "merge_strategy": "squash",
                "message": "msg",
                "close_source_branch": True,
            },
            (
                "merge",
                server.MergePullRequestParams(
                    pull_request_id=3, merge_strategy="squash", message="msg", close_source_branch=True
                ),
            ),
        ),
        (
            "decline_pull_request",
            {"pull_request_id": 4},
            ("decline", server.DeclinePullRequestParams(pull_request_id=4)),
        ),
    ],
)
async def test_call_tool_dispatch(monkeypatch, tool_name, arguments, expected_call):
    fake_client = FakeClient()
    monkeypatch.setattr(server, "init_client", lambda: fake_client)

    result = await server.call_tool(tool_name, arguments)

    assert result == f"{expected_call[0]}-result"
    last_call, params = fake_client.pull_requests.calls[-1]
    assert last_call == expected_call[0]
    assert isinstance(params, expected_call[1].__class__)
    assert params.model_dump() == expected_call[1].model_dump()


@pytest.mark.asyncio
async def test_call_tool_invalid_name(monkeypatch):
    monkeypatch.setattr(server, "init_client", lambda: FakeClient())

    with pytest.raises(ValueError):
        await server.call_tool("unknown_tool", {})


@pytest.mark.asyncio
async def test_list_tools_contains_expected_names():
    tools = await server.list_tools()

    names = [tool.name for tool in tools]
    assert names == [
        "get_pull_requests",
        "get_pull_request",
        "create_pull_request",
        "merge_pull_request_simple",
        "merge_pull_request",
        "decline_pull_request",
    ]
    assert all(tool.description for tool in tools)
    assert all(tool.inputSchema for tool in tools)


@pytest.mark.asyncio
async def test_main_uses_stdio_server(monkeypatch):
    read_stream = object()
    write_stream = object()
    run_calls: list[tuple[object, object, object]] = []
    options = {"init": "options"}

    async def fake_run(read, write, opts):
        run_calls.append((read, write, opts))

    @asynccontextmanager
    async def fake_stdio_server():
        yield read_stream, write_stream

    monkeypatch.setattr(server, "stdio_server", fake_stdio_server)
    monkeypatch.setattr(server.server, "create_initialization_options", lambda: options)
    monkeypatch.setattr(server.server, "run", fake_run)

    await server.main()

    assert run_calls == [(read_stream, write_stream, options)]
