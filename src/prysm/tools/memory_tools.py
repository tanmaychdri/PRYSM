"""
Tools that let the LLM explicitly read and write long-term memory mid-conversation.
"""

from typing import Any

from prysm.memory.long_term import LongTermMemory
from prysm.tools.interfaces import BaseTool


from prysm.users.session import UserSession

class MemoryTools(BaseTool):
    """Gives the LLM direct access to read/write long-term memory."""

    def __init__(self, memory: LongTermMemory, session: UserSession | None = None) -> None:
        self._memory = memory
        self._session = session

    def get_schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "remember",
                "description": (
                    "Save an important fact about the user to long-term memory. "
                    "Call this when the user explicitly asks you to remember something, "
                    "or when you learn a significant preference, project detail, or personal fact. "
                    "Do NOT call this to read memory — memory is already in your system prompt. "
                    "IMPORTANT: Always use the user's actual name in the fact (e.g., 'Tanmay prefers dark mode'), "
                    "never start with 'User'."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fact": {
                            "type": "string",
                            "description": "A concise, self-contained fact. E.g. 'Tanmay prefers dark mode'",
                        }
                    },
                    "required": ["fact"],
                },
            },
            {
                "name": "forget",
                "description": "Remove a specific fact from long-term memory when the user asks you to forget something.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fact": {
                            "type": "string",
                            "description": "The fact to remove.",
                        }
                    },
                    "required": ["fact"],
                },
            },
        ]

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        if tool_name == "remember":
            fact = arguments["fact"].strip()
            
            # Bulletproof intercept: replace generic "User" references with actual name
            if self._session and self._session.user:
                name = self._session.user.display_name
                if fact.startswith("User's "):
                    fact = f"{name}'s " + fact[7:]
                elif fact.startswith("User "):
                    fact = f"{name} " + fact[5:]
                elif fact.startswith("The user "):
                    fact = f"{name} " + fact[9:]

            added = self._memory.add_facts([fact])
            return f"Remembered: {fact}" if added else "Already knew that."

        if tool_name == "forget":
            fact = arguments["fact"].strip()
            facts = self._memory.get_facts()
            new_facts = [f for f in facts if f.lower() != fact.lower()]
            if len(new_facts) == len(facts):
                return f"Fact not found: {fact}"
            self._memory._facts = new_facts
            self._memory._save()
            return f"Forgotten: {fact}"

        raise ValueError(f"Unknown tool: {tool_name}")
