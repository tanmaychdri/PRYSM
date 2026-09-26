"""
Active user session — tracks who is currently logged in.
"""

from prysm.users.models import PRYSMUser, UserTier


class UserSession:
    """Holds the currently authenticated user for this PRYSM session."""

    def __init__(self) -> None:
        self._user: PRYSMUser | None = None

    @property
    def user(self) -> PRYSMUser | None:
        return self._user

    @property
    def is_authenticated(self) -> bool:
        return self._user is not None

    def login(self, user: PRYSMUser) -> None:
        self._user = user

    def logout(self) -> None:
        self._user = None

    def can_use_tool(self, tool_name: str) -> bool:
        if not self._user:
            return False
        return self._user.can_use_tool(tool_name)

    def require_tier(self, minimum: UserTier) -> bool:
        if not self._user:
            return False
        return self._user.tier.rank >= minimum.rank

    def display(self) -> str:
        if not self._user:
            return "Guest"
        tier_badge = {"god": "👑", "admin": "🛡", "user": "👤"}
        badge = tier_badge.get(self._user.tier.value, "")
        return f"{badge} {self._user.display_name}"
