import argparse
import asyncio
import logging
import sys
import time

import numpy as np

from prysm.core.container import ApplicationContainer
from prysm.models.interactions import UserInput
from prysm.users.auth_flow import run_auth_flow


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )


# ---------------------------------------------------------------------------
# Run modes
# ---------------------------------------------------------------------------

async def run_voice() -> None:
    """Full voice assistant mode: wake word -> STT -> LLM -> TTS."""
    setup_logging()
    logger = logging.getLogger("prysm.main")
    logger.info("Starting PRYSM in voice mode")

    container = ApplicationContainer()

    # Auth
    if not run_auth_flow(container.user_store, container.user_session):
        return

    voice_pipeline = container.build_voice()  # builds audio only here

    asyncio.create_task(container.assistant.run())
    await asyncio.sleep(0.3)
    await voice_pipeline.start()

    try:
        while not container.assistant._stop_event.is_set():
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await voice_pipeline.stop()
        await container.assistant.stop()


async def run_chat() -> None:
    """Interactive text chat mode (no audio)."""
    setup_logging()
    container = ApplicationContainer()

    # Auth — must login before chatting
    if not run_auth_flow(container.user_store, container.user_session):
        return

    assistant = container.assistant
    task = asyncio.create_task(assistant.run())
    await asyncio.sleep(0.3)

    user = container.user_session.user
    badge = {"god": "👑", "admin": "🛡️", "user": "👤"}.get(user.tier.value, "") if user else ""
    name = user.display_name if user else "Guest"

    print("\n╔══════════════════════════════╗")
    print(f"║   PRYSM  —  {badge} {name:<16}║")
    print("║   Type 'exit' to quit        ║")
    print("╚══════════════════════════════╝\n")

    try:
        while True:
            try:
                prompt = f"{name} > "
            user_text = input(prompt).strip()
            except EOFError:
                break
            if not user_text:
                continue
            if user_text.lower() in ("exit", "quit", "bye"):
                print("Goodbye.")
                break

            response = await assistant.process(UserInput(text=user_text, source="text"))
            if response and response.text:
                print(f"\nPRYSM > {response.text}\n")
            else:
                print("PRYSM > (no response)\n")
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await assistant.stop()
        await asyncio.sleep(0.1)
        task.cancel()


# ---------------------------------------------------------------------------
# Diagnostic utilities
# ---------------------------------------------------------------------------

async def test_mic() -> None:
    """Show live microphone volume levels."""
    setup_logging(logging.WARNING)
    container = ApplicationContainer()
    container.build_voice()
    await container.audio_in.start()
    print("Microphone test — speak into the mic (Ctrl+C to stop)\n")
    try:
        while True:
            chunk = await container.audio_in.read_chunk()
            arr = np.frombuffer(chunk, dtype=np.int16).astype(np.float32)
            rms = np.sqrt(np.mean(arr ** 2)) / 32768.0
            bars = int(rms * 500)
            print(f"\r[{'█' * bars:<50}] {rms:.4f}", end="", flush=True)
    except KeyboardInterrupt:
        print("\nDone.")
    finally:
        await container.audio_in.stop()


async def test_stt() -> None:
    """Record 5 seconds and transcribe."""
    setup_logging()
    container = ApplicationContainer()
    container.build_voice()
    print("Recording for 5 seconds — speak now...")
    await container.audio_in.start()

    frames: list[bytes] = []
    end = time.time() + 5.0
    while time.time() < end:
        frames.append(await container.audio_in.read_chunk())

    await container.audio_in.stop()
    print("Transcribing...")
    text = await container.stt.transcribe(b"".join(frames))
    print(f"\nResult: {text!r}")


async def test_tts(text: str) -> None:
    """Synthesize and play a text string."""
    setup_logging()
    container = ApplicationContainer()
    container.build_voice()
    if not container.settings.elevenlabs_api_key:
        print("Error: ELEVENLABS_API_KEY not set in .env")
        return
    print(f"Synthesizing: {text!r}")
    stream = await container.tts.synthesize(text)
    await container.audio_out.play_stream(stream)
    print("Done.")


def list_audio_devices() -> None:
    import sounddevice as sd
    print(sd.query_devices())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="prysm",
        description="PRYSM — modular async-first personal AI assistant",
    )
    parser.add_argument("--version", action="version", version="prysm 2.0.0")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("voice", help="Start in full voice mode (wake word + STT + TTS)")
    sub.add_parser("chat", help="Start interactive text chat")

    audio_p = sub.add_parser("audio", help="Audio utilities")
    audio_s = audio_p.add_subparsers(dest="audio_cmd")
    audio_s.add_parser("devices", help="List audio devices")
    audio_s.add_parser("test-mic", help="Live microphone volume meter")

    stt_p = sub.add_parser("stt", help="STT utilities")
    stt_s = stt_p.add_subparsers(dest="stt_cmd")
    stt_s.add_parser("test", help="Record 5s and transcribe")

    tts_p = sub.add_parser("tts", help="TTS utilities")
    tts_s = tts_p.add_subparsers(dest="tts_cmd")
    tts_test = tts_s.add_parser("test", help="Synthesize and play text")
    tts_test.add_argument("--text", default="Hello, I am PRYSM, your personal AI assistant.")

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    try:
        if args.command == "voice":
            asyncio.run(run_voice())
        elif args.command == "chat":
            asyncio.run(run_chat())
        elif args.command == "audio":
            if args.audio_cmd == "devices":
                list_audio_devices()
            elif args.audio_cmd == "test-mic":
                asyncio.run(test_mic())
        elif args.command == "stt":
            if args.stt_cmd == "test":
                asyncio.run(test_stt())
        elif args.command == "tts":
            if args.tts_cmd == "test":
                asyncio.run(test_tts(args.text))
        else:
            # Default: voice mode
            asyncio.run(run_voice())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
