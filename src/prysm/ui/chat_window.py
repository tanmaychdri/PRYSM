"""
PRYSM Chat UI — tkinter-based chat window.
Subscribes to EventBus for state updates, sends input to the assistant.
Run with: python -m prysm.ui.chat_window
"""

import asyncio
import logging
import threading
import tkinter as tk
from tkinter import scrolledtext

from prysm.core.container import ApplicationContainer
from prysm.core.events import (
    ErrorOccurred,
    ResponseGenerated,
    StateChanged,
)
from prysm.core.state import AssistantState
from prysm.models.interactions import UserInput

logger = logging.getLogger(__name__)

# ── Colours ──────────────────────────────────────────────────────────────────
BG = "#1a1a2e"
BG_CHAT = "#16213e"
BG_INPUT = "#0f3460"
FG = "#e0e0e0"
FG_USER = "#a8d8ea"
FG_PRYSM = "#f8c8d4"
FG_STATUS = "#888888"
ACCENT = "#e94560"
FONT_CHAT = ("Segoe UI", 11)
FONT_INPUT = ("Segoe UI", 11)
FONT_STATUS = ("Segoe UI", 9)


class ChatWindow:
    def __init__(self, container: ApplicationContainer, loop: asyncio.AbstractEventLoop) -> None:
        self._container = container
        self._loop = loop
        self._assistant = container.assistant

        # Subscribe to events
        container.event_bus.subscribe(ResponseGenerated, self._on_response)
        container.event_bus.subscribe(StateChanged, self._on_state_changed)
        container.event_bus.subscribe(ErrorOccurred, self._on_error)

        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.root = tk.Tk()
        self.root.title("PRYSM")
        self.root.configure(bg=BG)
        self.root.geometry("700x520")
        self.root.minsize(500, 400)

        # Header
        header = tk.Frame(self.root, bg=BG, pady=8)
        header.pack(fill=tk.X, padx=16)
        tk.Label(header, text="✦ PRYSM", font=("Segoe UI", 14, "bold"), bg=BG, fg=ACCENT).pack(side=tk.LEFT)
        self._status_var = tk.StringVar(value="● idle")
        tk.Label(header, textvariable=self._status_var, font=FONT_STATUS, bg=BG, fg=FG_STATUS).pack(side=tk.RIGHT)

        # Chat area
        self._chat = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg=BG_CHAT,
            fg=FG,
            font=FONT_CHAT,
            relief=tk.FLAT,
            padx=12,
            pady=8,
            insertbackground=FG,
        )
        self._chat.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 6))
        self._chat.tag_config("user", foreground=FG_USER)
        self._chat.tag_config("prysm", foreground=FG_PRYSM)
        self._chat.tag_config("system", foreground=FG_STATUS, font=("Segoe UI", 9, "italic"))

        # Input row
        input_frame = tk.Frame(self.root, bg=BG, pady=6)
        input_frame.pack(fill=tk.X, padx=12, pady=(0, 10))

        self._input_var = tk.StringVar()
        self._entry = tk.Entry(
            input_frame,
            textvariable=self._input_var,
            font=FONT_INPUT,
            bg=BG_INPUT,
            fg=FG,
            insertbackground=FG,
            relief=tk.FLAT,
        )
        self._entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 8))
        self._entry.bind("<Return>", self._on_send)

        send_btn = tk.Button(
            input_frame,
            text="Send",
            command=self._on_send,
            bg=ACCENT,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=14,
            pady=6,
            cursor="hand2",
        )
        send_btn.pack(side=tk.RIGHT)

        self._entry.focus()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._append("system", "PRYSM is ready. Type a message or speak after the wake word.\n")

    # ── Chat helpers ──────────────────────────────────────────────────────────

    def _append(self, tag: str, text: str) -> None:
        self._chat.configure(state=tk.NORMAL)
        self._chat.insert(tk.END, text, tag)
        self._chat.configure(state=tk.DISABLED)
        self._chat.see(tk.END)

    def _set_status(self, text: str) -> None:
        self._status_var.set(f"● {text}")

    # ── User input ────────────────────────────────────────────────────────────

    def _on_send(self, _event=None) -> None:
        text = self._input_var.get().strip()
        if not text:
            return
        self._input_var.set("")
        self._append("user", f"You  › {text}\n")
        asyncio.run_coroutine_threadsafe(
            self._assistant.process(UserInput(text=text, source="text")),
            self._loop,
        )

    # ── Event handlers (called from async loop, schedule UI update on main thread) ──

    async def _on_response(self, event: ResponseGenerated) -> None:
        self.root.after(0, self._append, "prysm", f"PRYSM › {event.response_text}\n\n")

    async def _on_state_changed(self, event: StateChanged) -> None:
        label = event.new_state.name.lower().replace("_", " ")
        self.root.after(0, self._set_status, label)

    async def _on_error(self, event: ErrorOccurred) -> None:
        self.root.after(0, self._append, "system", f"[error] {event.error_message}\n")

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def _on_close(self) -> None:
        asyncio.run_coroutine_threadsafe(self._assistant.stop(), self._loop)
        self.root.after(300, self.root.destroy)

    def run(self) -> None:
        self.root.mainloop()


# ── Entry point ───────────────────────────────────────────────────────────────

def launch_chat_ui() -> None:
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    loop = asyncio.new_event_loop()

    def run_loop():
        asyncio.set_event_loop(loop)
        loop.run_forever()

    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()

    container = ApplicationContainer()

    # Start assistant in the background loop
    asyncio.run_coroutine_threadsafe(container.assistant.run(), loop)

    window = ChatWindow(container, loop)
    window.run()

    loop.call_soon_threadsafe(loop.stop)


if __name__ == "__main__":
    launch_chat_ui()
