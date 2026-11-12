import httpx
import pytest

from companion.adapters.clerk.accounts import ClerkAccounts


def accounts_answering(
    status_code: int, requests: list[httpx.Request]
) -> ClerkAccounts:
    """Build Clerk accounts whose API calls are recorded and answered."""

    def clerk_api(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(status_code, json={})

    return ClerkAccounts(
        "sk_test_123",
        http_client=httpx.Client(transport=httpx.MockTransport(clerk_api)),
    )


def test_deleting_an_account_calls_clerks_delete_user_api() -> None:
    requests: list[httpx.Request] = []
    accounts = accounts_answering(200, requests)

    accounts.delete_account("user_abc")

    assert [(request.method, str(request.url)) for request in requests] == [
        ("DELETE", "https://api.clerk.com/v1/users/user_abc")
    ]
    assert requests[0].headers["Authorization"] == "Bearer sk_test_123"
    assert requests[0].headers["User-Agent"] == "companion-backend"


def test_an_account_already_gone_from_clerk_counts_as_deleted() -> None:
    accounts = accounts_answering(404, [])

    accounts.delete_account("user_abc")


def test_a_clerk_failure_is_raised() -> None:
    accounts = accounts_answering(500, [])

    with pytest.raises(httpx.HTTPStatusError):
        accounts.delete_account("user_abc")
