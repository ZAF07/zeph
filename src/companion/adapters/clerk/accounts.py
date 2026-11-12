import httpx

from companion.adapters.clerk.auth_verifier import CLERK_API_URL, USER_AGENT


class ClerkAccounts:
    """Manages accounts in Clerk through its Backend API."""

    def __init__(
        self, secret_key: str, http_client: httpx.Client | None = None
    ) -> None:
        """Set up the client.

        Args:
            secret_key: The Clerk secret key. Requests carry a User-Agent
                because Clerk refuses Python's default one.
            http_client: The HTTP client to use; a new one is made if not given.
        """
        self._auth_header = {
            "Authorization": f"Bearer {secret_key}",
            "User-Agent": USER_AGENT,
        }
        self._http = http_client or httpx.Client(timeout=10)

    def delete_account(self, auth_id: str) -> None:
        """Delete a Clerk user, so they can't sign in again.

        A user Clerk no longer has counts as deleted.

        Args:
            auth_id: The Clerk user ID.

        Raises:
            httpx.HTTPStatusError: If Clerk refuses or fails.
        """
        response = self._http.delete(
            f"{CLERK_API_URL}/users/{auth_id}", headers=self._auth_header
        )
        if response.status_code != httpx.codes.NOT_FOUND:
            response.raise_for_status()
