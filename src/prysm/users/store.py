"""
User store — loads/saves users from data/users.json.
PINs are stored as SHA-256 hashes, never plain text.
"""

import hashlib
import json
import logging
from pathlib import Path

from prysm.users.models import PRYSMUser, UserTier

logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"

GOD_USERNAME = "tanmay"


def _hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.strip().encode()).hexdigest()


class UserStore:
    """Persistent user registry."""

    def __init__(self, path: Path = USERS_FILE) -> None:
        self._path = path
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._users: dict[str, PRYSMUser] = {}
        self._load()
        self._ensure_god_user()

    # ------------------------------------------------------------------
    # Load / save
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            for u in raw.get("users", []):
                user = PRYSMUser(**u)
                self._users[user.username.lower()] = user
            logger.info(f"Loaded {len(self._users)} users")
        except Exception:
            logger.exception("Failed to load users")

    def _save(self) -> None:
        try:
            data = {"users": [u.model_dump() for u in self._users.values()]}
            self._path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception:
            logger.exception("Failed to save users")

    def _ensure_god_user(self) -> None:
        """Create Tanmay's god account on first run if it doesn't exist."""
        if GOD_USERNAME not in self._users:
            logger.info("Creating god user 'tanmay' — set your PIN on first login")
            god = PRYSMUser(
                username=GOD_USERNAME,
                display_name="Tanmay",
                tier=UserTier.GOD,
                pin_hash="",   # empty = no PIN set yet, will be prompted
            )
            self._users[GOD_USERNAME] = god
            self._save()

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def authenticate(self, username: str, pin: str) -> PRYSMUser | None:
        """Return user if credentials match, else None."""
        user = self._users.get(username.lower())
        if not user:
            return None
        # If no PIN set yet, any PIN sets it (first login)
        if not user.pin_hash:
            return None  # must go through set_pin flow
        if user.pin_hash == _hash_pin(pin):
            return user
        return None

    def needs_pin_setup(self, username: str) -> bool:
        user = self._users.get(username.lower())
        return user is not None and not user.pin_hash

    def set_pin(self, username: str, pin: str) -> bool:
        """Set or change a user's PIN. Returns True on success."""
        user = self._users.get(username.lower())
        if not user:
            return False
        if len(pin.strip()) < 4:
            return False
        user.pin_hash = _hash_pin(pin)
        self._save()
        return True

    # ------------------------------------------------------------------
    # User management (god/admin only — enforced at call site)
    # ------------------------------------------------------------------

    def get_user(self, username: str) -> PRYSMUser | None:
        return self._users.get(username.lower())

    def list_users(self) -> list[PRYSMUser]:
        return list(self._users.values())

    def add_user(
        self,
        username: str,
        display_name: str,
        tier: UserTier,
        pin: str,
    ) -> PRYSMUser | None:
        if username.lower() in self._users:
            logger.warning(f"User '{username}' already exists")
            return None
        if len(pin.strip()) < 4:
            return None
        user = PRYSMUser(
            username=username.lower(),
            display_name=display_name,
            tier=tier,
            pin_hash=_hash_pin(pin),
        )
        self._users[username.lower()] = user
        self._save()
        logger.info(f"Created user '{username}' with tier '{tier}'")
        return user

    def remove_user(self, username: str) -> bool:
        key = username.lower()
        if key == GOD_USERNAME:
            logger.warning("Cannot remove god user")
            return False
        if key not in self._users:
            return False
        del self._users[key]
        self._save()
        return True

    def set_tier(self, username: str, tier: UserTier) -> bool:
        key = username.lower()
        if key == GOD_USERNAME:
            logger.warning("Cannot change god user's tier")
            return False
        user = self._users.get(key)
        if not user:
            return False
        user.tier = tier
        self._save()
        return True
