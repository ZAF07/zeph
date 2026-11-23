from companion.core.models import AccountIdentity

LOAD_TEST_TOKEN_PREFIX = "load-test-"


class LoadTestAccounts:
    """Sign-in for load tests: a token naming a load-test account signs in as it.

    The token is the account's auth ID, which must start with "load-test-",
    so the load-test script can call Dashboard API pages with no auth
    provider. Deleting an account does nothing.
    """

    def verify(self, token: str) -> AccountIdentity | None:
        """Sign in as the load-test account the token names.

        Args:
            token: The bearer token, e.g. "load-test-admin".

        Returns:
            The account; None for a token that isn't a load-test one.
        """
        if not token.startswith(LOAD_TEST_TOKEN_PREFIX):
            return None
        return AccountIdentity(auth_id=token, email=f"{token}@load-test.invalid")

    def delete_account(self, auth_id: str) -> None:
        """Do nothing; load-test accounts exist only in the database.

        Args:
            auth_id: The account's ID.
        """
