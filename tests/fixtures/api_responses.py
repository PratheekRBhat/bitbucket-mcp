"""Mock API response data for testing."""

# Realistic Bitbucket API responses for various scenarios

PULL_REQUEST_OPEN = {
    "id": 1,
    "title": "Implement user authentication",
    "summary": {"raw": "This PR implements JWT-based authentication for the API"},
    "state": "OPEN",
    "author": {"display_name": "John Doe"},
    "source": {
        "repository": {"type": "repository"},
        "branch": {"name": "feature/auth"},
        "commit": {"hash": "a1b2c3d4e5f6"},
    },
    "destination": {
        "repository": {"type": "repository"},
        "branch": {"name": "develop"},
        "commit": {"hash": "f6e5d4c3b2a1"},
    },
}

PULL_REQUEST_MERGED = {
    "id": 2,
    "title": "Fix database connection pool leak",
    "summary": {"raw": "Resolves issue #42 by properly closing connections"},
    "state": "MERGED",
    "merge_commit": {"hash": "9876543210ab"},
    "author": {"display_name": "Jane Smith"},
    "source": {
        "repository": {"type": "repository"},
        "branch": {"name": "bugfix/db-leak"},
        "commit": {"hash": "1a2b3c4d5e6f"},
    },
    "destination": {
        "repository": {"type": "repository"},
        "branch": {"name": "main"},
        "commit": {"hash": "6f5e4d3c2b1a"},
    },
}

PULL_REQUEST_DECLINED = {
    "id": 3,
    "title": "Experimental feature - needs more work",
    "summary": {"raw": "This approach didn't work out as expected"},
    "state": "DECLINED",
    "reason": "Needs redesign",
    "author": {"display_name": "Bob Johnson"},
    "source": {
        "repository": {"type": "repository"},
        "branch": {"name": "experiment/new-approach"},
        "commit": {"hash": "abc123def456"},
    },
    "destination": {
        "repository": {"type": "repository"},
        "branch": {"name": "develop"},
        "commit": {"hash": "456def123abc"},
    },
}

PULL_REQUEST_LIST_RESPONSE = {
    "values": [
        PULL_REQUEST_OPEN,
        {
            "id": 4,
            "title": "Update dependencies",
            "summary": {"raw": "Bump all dependencies to latest versions"},
            "state": "OPEN",
            "author": {"display_name": "Pratheek Bhat"},
            "source": {
                "repository": {"type": "repository"},
                "branch": {"name": "chore/deps-update"},
                "commit": {"hash": "deps001"},
            },
            "destination": {
                "repository": {"type": "repository"},
                "branch": {"name": "main"},
                "commit": {"hash": "main001"},
            },
        },
    ],
    "size": 2,
    "page": 1,
    "pagelen": 10,
}

EMPTY_PULL_REQUEST_LIST = {"values": [], "size": 0, "page": 1, "pagelen": 10}
