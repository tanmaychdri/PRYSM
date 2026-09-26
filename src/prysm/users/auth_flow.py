"""
Terminal authentication flow — handles login, first-time PIN setup.
Called at startup of chat/voice mode before the assistant runs.
"""

import getpass
import logging

from prysm.users.models import PRYSMUser
from prysm.users.session import UserSession
from prysm.users.store import UserStore

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3


def run_auth_flow(store: UserStore, session: UserSession) -> bool:
    """
    Interactive terminal login.
    Returns True if login succeeded, False if user cancelled or exceeded attempts.
    """
    print("\n┌─────────────────────────────┐")
    print("│        PRYSM  Login         │")
    print("└─────────────────────────────┘")

    username = input("Username: ").strip().lower()
    if not username:
        print("Cancelled.")
        return False

    user = store.get_user(username)
    if not user:
        print(f"  ✗ User '{username}' not found.")
        return False

    # First-time PIN setup
    if store.needs_pin_setup(username):
        print(f"\n  Welcome, {user.display_name}! This is your first login.")
        print("  Please set a PIN (minimum 4 digits):")
        pin = getpass.getpass("  New PIN: ").strip()
        confirm = getpass.getpass("  Confirm PIN: ").strip()
        if pin != confirm:
            print("  ✗ PINs do not match.")
            return False
        if not store.set_pin(username, pin):
            print("  ✗ PIN must be at least 4 characters.")
            return False
        print(f"  ✓ PIN set. Welcome, {user.display_name}!")
        # Re-fetch after save
        user = store.get_user(username)

    # Normal login
    for attempt in range(1, MAX_ATTEMPTS + 1):
        pin = getpass.getpass(f"  PIN ({attempt}/{MAX_ATTEMPTS}): ").strip()
        authenticated = store.authenticate(username, pin)
        if authenticated:
            session.login(authenticated)
            tier_badge = {"god": "👑", "admin": "🛡️", "user": "👤"}
            badge = tier_badge.get(authenticated.tier.value, "")
            print(f"\n  ✓ Welcome back, {badge} {authenticated.display_name}!\n")
            return True
        print("  ✗ Incorrect PIN.")

    print("  Too many failed attempts. Exiting.")
    return False
