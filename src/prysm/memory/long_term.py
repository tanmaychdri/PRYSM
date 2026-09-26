"""
Long-term memory: extracts and persists facts about the user across sessions.

Facts are stored in data/memory.json as a flat list of strings, e.g.:
  - "User's name is Tanmay"
  - "User is building an AI assistant called PRYSM in Python"
  - "User prefers dark themes"
  - "User dislikes verbose responses"
  - "Project: PRYSM — rebuilt from scratch on 2026-09-26, uses Groq LLM, ElevenLabs TTS, FasterWhisper STT"

The LLM extracts new facts after every exchange. Duplicates are deduplicated.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
MEMORY_FILE = DATA_DIR / "memory.json"

EXTRACTION_PROMPT = """You are a memory extraction assistant. 
Given the conversation below, extract any NEW facts worth remembering long-term about {user_name}.
Focus on:
- Personal info (name, preferences, dislikes, habits)
- Projects they are working on (name, tech stack, progress, decisions made)
- Code or technical decisions made during the session
- Goals and plans they mentioned
- Anything they explicitly asked you to remember

IMPORTANT: Always refer to the user by their name "{user_name}" in facts, NOT as "the user" or "User".
For example, write "{user_name} prefers dark themes" instead of "User prefers dark themes".
Write "{user_name}'s friend Aniket" instead of "User's friend Aniket".

Return ONLY a JSON array of short fact strings. Each fact must be self-contained and specific.
If there is nothing new to remember, return an empty array [].
Do NOT repeat facts that are already in the existing memory (listed below).
Do NOT include trivial small talk.

Existing memory (do not repeat these):
{existing}

Conversation:
{conversation}

Return only valid JSON, nothing else."""


class LongTermMemory:
    """
    Extracts, stores, and retrieves long-term facts about the user.
    Uses the LLM to extract facts after each session.
    """

    def __init__(self, path: Path = MEMORY_FILE) -> None:
        self._path = path
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._facts: list[str] = self._load()

    def _load(self) -> list[str]:
        if not self._path.exists():
            return []
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            facts = data.get("facts", [])
            logger.info(f"Loaded {len(facts)} long-term memory facts")
            return facts
        except Exception:
            logger.exception("Failed to load long-term memory")
            return []

    def _save(self) -> None:
        try:
            self._path.write_text(
                json.dumps({"facts": self._facts}, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            logger.exception("Failed to save long-term memory")

    def get_facts(self) -> list[str]:
        return list(self._facts)

    def add_facts(self, new_facts: list[str]) -> int:
        """Add new facts, skipping duplicates. Returns count added."""
        added = 0
        existing_lower = {f.lower() for f in self._facts}
        for fact in new_facts:
            fact = fact.strip()
            if fact and fact.lower() not in existing_lower:
                self._facts.append(fact)
                existing_lower.add(fact.lower())
                added += 1
        if added:
            self._save()
            logger.info(f"Added {added} new memory facts")
        return added

    def format_for_prompt(self) -> str:
        """Format facts as a bullet list for injection into the system prompt."""
        if not self._facts:
            return "(no long-term memories yet)"
        return "\n".join(f"- {f}" for f in self._facts)

    async def extract_and_store(
        self,
        conversation_text: str,
        llm_provider,
        user_name: str = "the user",
    ) -> int:
        """
        Ask the LLM to extract new facts from the conversation and store them.
        Returns the number of new facts added.
        """
        from prysm.models.interactions import LLMMessage

        existing_formatted = self.format_for_prompt()
        prompt = EXTRACTION_PROMPT.format(
            existing=existing_formatted,
            conversation=conversation_text,
            user_name=user_name,
        )

        try:
            response = await llm_provider.generate_response(
                [LLMMessage(role="user", content=prompt)],
                tools=None,
            )
            text = (response.text or "").strip()

            # Strip markdown code fences if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            new_facts: list[str] = json.loads(text)
            if not isinstance(new_facts, list):
                return 0
                
            # Bulletproof intercept: replace generic "User" if the LLM ignored instructions
            cleaned_facts = []
            for fact in new_facts:
                if fact.startswith("User's "):
                    fact = f"{user_name}'s " + fact[7:]
                elif fact.startswith("User "):
                    fact = f"{user_name} " + fact[5:]
                elif fact.startswith("The user "):
                    fact = f"{user_name} " + fact[9:]
                cleaned_facts.append(fact)
                
            return self.add_facts(cleaned_facts)

        except json.JSONDecodeError:
            logger.warning("Memory extraction returned invalid JSON")
            return 0
        except Exception:
            logger.exception("Memory extraction failed")
            return 0
