from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from companion.core.models import User, UserRole
from companion.core.ports import AuthVerifier
from companion.core.users import UserService


def build_current_user_dependency(
    auth_verifier: AuthVerifier, user_service: UserService
) -> Callable[..., User]:
    """Build the FastAPI dependency that finds the User making a request.

    Args:
        auth_verifier: Checks bearer tokens.
        user_service: Finds or creates the User behind a token.

    Returns:
        The dependency.
    """

    def current_user(authorization: Annotated[str | None, Header()] = None) -> User:
        """Find the User making the request, creating them on first visit.

        Args:
            authorization: The `Authorization: Bearer <token>` header.

        Returns:
            The User.

        Raises:
            HTTPException: 401 if the token is missing or not valid.
        """
        scheme, _, token = (authorization or "").partition(" ")
        identity = auth_verifier.verify(token) if scheme == "Bearer" else None
        if identity is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")
        return user_service.get_or_create(identity)

    return current_user


def build_current_admin_dependency(
    current_user: Callable[..., User],
) -> Callable[..., User]:
    """Build the FastAPI dependency that lets only Admins through.

    Args:
        current_user: The dependency that finds the User making a request.

    Returns:
        The dependency.
    """

    def current_admin(user: Annotated[User, Depends(current_user)]) -> User:
        """Check that the User making the request is an Admin.

        Args:
            user: The signed-in User.

        Returns:
            The Admin.

        Raises:
            HTTPException: 403 if the User is not an Admin.
        """
        if user.role != UserRole.ADMIN:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Admins only")
        return user

    return current_admin
