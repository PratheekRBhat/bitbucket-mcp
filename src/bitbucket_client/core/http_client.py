from .base_client import BaseClient


class HttpClient(BaseClient):
    """
    The specific HTTP client for interacting with the Bitbucket Cloud API.

    This class inherits from the generic BaseClient and configures it
    with Bitbucket's specific URL and authentication headers.
    """

    def __init__(self, workspace: str, repo_slug: str, auth_token: str):
        """
        Initializes the Bitbucket-specific HTTP client.

        Args:
            workspace: The Bitbucket workspace ID.
            repo_slug: The repository slug.
            auth_token: The App Password or Bearer Token for authentication.
        """
        base_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/"

        # Here is where we build the Bitbucket-specific headers
        headers = {
            # Note: If you are using an OAuth token, 'Bearer' is correct.
            # If you are using an App Password with your username,
            # you should use Basic Auth instead.
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "bitbucket-mcp",
        }

        # We now call the parent class's __init__ with the prepared config
        super().__init__(base_url=base_url, headers=headers)
