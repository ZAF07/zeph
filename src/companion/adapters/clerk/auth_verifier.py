import httpx
import jwt

from companion.core.models import AccountIdentity

CLERK_API_URL = "https://api.clerk.com/v1"
USER_AGENT = "companion-backend"


def clerk_api_headers(secret_key: str) -> dict[str, str]:
    """Build the headers every Clerk Backend API request carries.

    Requests carry a User-Agent because Clerk refuses Python's default one.

    Args:
        secret_key: The Clerk secret key.

    Returns:
        The Authorization and User-Agent headers.
    """
    return {"Authorization": f"Bearer {secret_key}", "User-Agent": USER_AGENT}


class ClerkAuthVerifier:
    """Verifies Clerk session tokens sent by the Dashboard."""

    def __init__(
        self,
        secret_key: str,
        authorized_parties: list[str],
        http_client: httpx.Client | None = None,
    ) -> None:
        """Set up the verifier.

        Args:
            secret_key: The Clerk secret key, used to fetch signing keys and
                account emails. Requests carry a User-Agent because Clerk
                refuses Python's default one.
            authorized_parties: Origins allowed in the token's `azp` claim.
            http_client: The HTTP client to use; a new one is made if not given.
        """
        self._auth_header = clerk_api_headers(secret_key)
        self._authorized_parties = authorized_parties
        self._http = http_client or httpx.Client(timeout=10)
        self._signing_keys = jwt.PyJWKClient(
            f"{CLERK_API_URL}/jwks", headers=self._auth_header
        )
        self._emails_by_account: dict[str, str | None] = {}

    def verify(self, token: str) -> AccountIdentity | None:
        """Check a Clerk session token.

        Args:
            token: The bearer token from the request.

        Returns:
            The account identity, or None if the token is not valid.

        Raises:
            jwt.PyJWKClientConnectionError: If Clerk's signing keys can't be
                fetched; that is our fault, not the caller's.
        """
        try:
            signing_key = self._signing_keys.get_signing_key_from_jwt(token)
            claims = jwt.decode(token, signing_key.key, algorithms=["RS256"])
        except jwt.PyJWKClientConnectionError:
            raise
        except jwt.PyJWTError:
            return None
        authorized_party = claims.get("azp")
        if authorized_party and authorized_party not in self._authorized_parties:
            return None
        account_id: str = claims["sub"]
        return AccountIdentity(auth_id=account_id, email=self._email_for(account_id))

    def _email_for(self, account_id: str) -> str | None:
        """Look up an account's primary email, remembering it after the first time.

        Args:
            account_id: The Clerk user ID.

        Returns:
            The primary email address, or None if it has none.
        """
        if account_id not in self._emails_by_account:
            response = self._http.get(
                f"{CLERK_API_URL}/users/{account_id}", headers=self._auth_header
            )
            response.raise_for_status()
            account = response.json()
            primary_id = account.get("primary_email_address_id")
            self._emails_by_account[account_id] = next(
                (
                    address["email_address"]
                    for address in account.get("email_addresses", [])
                    if address["id"] == primary_id
                ),
                None,
            )
        return self._emails_by_account[account_id]
