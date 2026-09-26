"""
User data models and permission tiers.

Tiers (highest to lowest):
  god   — Tanmay. Full access. Can manage all users. Cannot be demoted or deleted.
  admin — Can use all OS tools. Can manage normal users.
  user  — Chat only. No OS control, no shell, no power commands.
"""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class UserTier(str, Enum):
    GOD = "god"
    ADMIN = "admin"
    USER = "user"

    def __str__(self) -> str:
        return self.value

    @property
    def rank(self) -> int:
        return {"god": 3, "admin": 2, "user": 1}[self.value]

    def can_manage(self, other: "UserTier") -> bool:
        """True if this tier can promote/demote/delete the other tier."""
        return self.rank > other.rank


# Tools blocked per tier — god has no restrictions
BLOCKED_TOOLS: dict[UserTier, set[str]] = {
    UserTier.USER: {
        # OS control
        "run_shell_command",
        "power_action",
        "open_application",
        "open_url",
        "set_volume",
        "mute_volume",
        # Memory management (users can't modify global memory)
        "remember",
        "forget",
    },
    UserTier.ADMIN: set(),   # admins can use everything
    UserTier.GOD: set(),     # god can use everything
}


class PRYSMUser(BaseModel):
    username: str
    display_name: str
    tier: UserTier
    pin_hash: str                          # SHA-256 hex of PIN
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_god(self) -> bool:
        return self.tier == UserTier.GOD

    @property
    def is_admin(self) -> bool:
        return self.tier in (UserTier.GOD, UserTier.ADMIN)

    def blocked_tools(self) -> set[str]:
        return BLOCKED_TOOLS.get(self.tier, set())

    def can_use_tool(self, tool_name: str) -> bool:
        return tool_name not in self.blocked_tools()
