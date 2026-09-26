"""
User management tools — only available to god and admin tier users.
Enforced at the ToolExecutor level via UserSession.
"""

from typing import Any

from prysm.tools.interfaces import BaseTool
from prysm.users.models import UserTier
from prysm.users.session import UserSession
from prysm.users.store import UserStore


class UserManagementTools(BaseTool):
    """Lets god/admin manage PRYSM users via natural language."""

    def __init__(self, store: UserStore, session: UserSession) -> None:
        self._store = store
        self._session = session

    def get_schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "list_users",
                "description": "List all PRYSM users, their tiers, and status.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "add_user",
                "description": "Create a new PRYSM user with a username, display name, tier, and PIN.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string", "description": "Login username (no spaces)."},
                        "display_name": {"type": "string", "description": "Friendly display name."},
                        "tier": {
                            "type": "string",
                            "enum": ["admin", "user"],
                            "description": "User tier. 'admin' or 'user'. Only god can create admins.",
                        },
                        "pin": {"type": "string", "description": "Initial PIN (min 4 digits)."},
                    },
                    "required": ["username", "display_name", "tier", "pin"],
                },
            },
            {
                "name": "remove_user",
                "description": "Delete a PRYSM user by username.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string", "description": "Username to remove."}
                    },
                    "required": ["username"],
                },
            },
            {
                "name": "set_user_tier",
                "description": "Change a user's permission tier.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string"},
                        "tier": {
                            "type": "string",
                            "enum": ["admin", "user"],
                            "description": "New tier for the user.",
                        },
                    },
                    "required": ["username", "tier"],
                },
            },
            {
                "name": "reset_user_pin",
                "description": "Reset a user's PIN to a new value.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string"},
                        "new_pin": {"type": "string", "description": "New PIN (min 4 digits)."},
                    },
                    "required": ["username", "new_pin"],
                },
            },
        ]

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        actor = self._session.user
        if not actor:
            return "Error: not authenticated."

        if tool_name == "list_users":
            users = self._store.list_users()
            if not users:
                return "No users found."
            lines = []
            for u in users:
                badge = {"god": "👑", "admin": "🛡", "user": "👤"}.get(u.tier.value, "")
                pin_status = "PIN set" if u.pin_hash else "⚠ no PIN"
                lines.append(f"{badge} {u.display_name} (@{u.username}) — {u.tier.value} — {pin_status}")
            return "\n".join(lines)

        if tool_name == "add_user":
            username = arguments["username"].strip().lower()
            display_name = arguments["display_name"].strip()
            tier_str = arguments["tier"].strip().lower()
            pin = str(arguments["pin"]).strip()

            # Only god can create admins
            if tier_str == "admin" and not actor.is_god:
                return "Permission denied: only the god user can create admin accounts."

            tier = UserTier(tier_str)

            # Admins can only create users below their own tier
            if not actor.tier.can_manage(tier) and not actor.is_god:
                return f"Permission denied: you cannot create a '{tier_str}' user."

            user = self._store.add_user(username, display_name, tier, pin)
            if not user:
                return f"Failed: user '{username}' may already exist or PIN is too short."
            return f"✓ Created user '{display_name}' (@{username}) with tier '{tier_str}'."

        if tool_name == "remove_user":
            username = arguments["username"].strip().lower()
            target = self._store.get_user(username)
            if not target:
                return f"User '{username}' not found."
            if not actor.tier.can_manage(target.tier):
                return f"Permission denied: you cannot remove a '{target.tier.value}' user."
            success = self._store.remove_user(username)
            return f"✓ Removed user '@{username}'." if success else "Failed to remove user."

        if tool_name == "set_user_tier":
            username = arguments["username"].strip().lower()
            new_tier = UserTier(arguments["tier"].strip().lower())
            target = self._store.get_user(username)
            if not target:
                return f"User '{username}' not found."
            if not actor.tier.can_manage(target.tier):
                return f"Permission denied: you cannot modify a '{target.tier.value}' user."
            if not actor.tier.can_manage(new_tier) and not actor.is_god:
                return f"Permission denied: you cannot assign tier '{new_tier.value}'."
            success = self._store.set_tier(username, new_tier)
            return f"✓ @{username} is now '{new_tier.value}'." if success else "Failed."

        if tool_name == "reset_user_pin":
            username = arguments["username"].strip().lower()
            new_pin = str(arguments["new_pin"]).strip()
            target = self._store.get_user(username)
            if not target:
                return f"User '{username}' not found."
            # Users can reset their own PIN; admins/god can reset others below them
            if username != actor.username and not actor.tier.can_manage(target.tier):
                return "Permission denied."
            success = self._store.set_pin(username, new_pin)
            return f"✓ PIN reset for @{username}." if success else "PIN must be at least 4 characters."

        raise ValueError(f"Unknown tool: {tool_name}")
