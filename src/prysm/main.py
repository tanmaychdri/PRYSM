import argparse
import asyncio
import logging
import sys
import time

import numpy as np
import sounddevice as sd

from prysm.core.container import ApplicationContainer
from prysm.models.interactions import UserInput


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )


async def async_main():
    setup_logging()
    logger = logging.getLogger("prysm.main")
    logger.info("Starting PRYSM")

    container = ApplicationContainer()

    # Start both Assistant Core and Voice Pipeline
    asyncio.create_task(container.assistant.run())
    await asyncio.sleep(0.5)
    await container.voice_pipeline.start()
    await container.mobile_service.start()

    try:
        # Keep main running until stopped
        while not container.assistant._stop_event.is_set():
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    finally:
        await container.voice_pipeline.stop()
        await container.assistant.stop()


async def run_chat():
    setup_logging()
    container = ApplicationContainer()
    assistant = container.assistant

    task = asyncio.create_task(assistant.run())
    await asyncio.sleep(0.5)
    await container.mobile_service.start()

    print("\nPRYSM Development Console")
    print("Type 'exit' to quit.\n")

    try:
        while True:
            user_text = input("You > ")
            if user_text.strip().lower() == "exit":
                print("Shutting down PRYSM...")
                break

            input_model = UserInput(text=user_text, source="cli")
            response = await assistant.process(input_model)
            if response:
                print(f"PRYSM > {response.text}")
    except (KeyboardInterrupt, EOFError):
        print("\nShutting down PRYSM...")
    finally:
        await assistant.stop()
        await asyncio.sleep(0.2)
        task.cancel()


def list_devices():
    print("Available Audio Devices:\n")
    print(sd.query_devices())


async def test_input():
    print("Testing audio input... Speak into the microphone (press Ctrl+C to stop).")
    setup_logging()
    container = ApplicationContainer()
    cap = container.audio_in
    await cap.start()
    try:
        while True:
            chunk = await cap.read_chunk()
            arr = np.frombuffer(chunk, dtype=np.int16)
            rms = np.sqrt(np.mean(arr.astype(np.float32) ** 2))
            vol = int(rms / 32768.0 * 50)
            print(f"Volume: [{'#' * vol}{' ' * (50 - vol)}] {rms:.2f}", end="\r")
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        await cap.stop()


async def test_stt():
    print("Testing STT... Loading model (this may take a moment)...")
    setup_logging()
    container = ApplicationContainer()

    print("\nSay something (recording for 5 seconds)...")
    await container.audio_in.start()

    frames = []
    end_time = time.time() + 5.0
    while time.time() < end_time:
        chunk = await container.audio_in.read_chunk()
        frames.append(chunk)

    await container.audio_in.stop()
    audio_data = b"".join(frames)

    print("Transcribing...")
    text = await container.stt.transcribe(audio_data)
    print(f"\nTranscription Result:\n{text}")


async def test_tts(text: str):
    setup_logging()
    container = ApplicationContainer()
    if not container.settings.elevenlabs_api_key:
        print("Error: ELEVENLABS_API_KEY is not configured in .env")
        return

    print(f"Synthesizing: '{text}'")
    stream = container.tts.synthesize(text)

    print("Playing audio...")
    await container.audio_out.play_stream(stream)
    print("Done.")


async def run_device_command(args):
    setup_logging()
    container = ApplicationContainer()

    if args.device_cmd == "pair":
        code = container.mobile_service.begin_pairing()
        print(f"\n[PAIRING] Enter this code on your Android device: {code}\n")
        await container.mobile_service.start()
        print("Waiting for device to connect... (Press Ctrl+C to cancel)")
        try:
            while container.mobile_service.server.active_pairing_code:
                await asyncio.sleep(1)
            print("Pairing complete.")
        except KeyboardInterrupt:
            print("Cancelled.")

    elif args.device_cmd == "list":
        devices = container.mobile_service.registry.get_all_devices()
        print("\nPaired Devices:")
        for d in devices:
            print(
                f"- {d.name} ({d.device_id}) [Platform: {d.platform}] - Last Seen: {d.last_seen}"
            )

    elif args.device_cmd == "revoke":
        from prysm.tools.mobile.device import MobileDeviceTools

        tools = MobileDeviceTools(container.mobile_service)
        res = await tools.revoke_device(args.device_id)
        print(res.get("message"))

    elif args.device_cmd == "status":
        await container.mobile_service.start()
        # Give server time to bind, wait for device heartbeat maybe, but device might not connect immediately
        print(f"Connecting to fetch status for {args.device_id}...")
        # Since it's CLI, maybe just print a warning that device might be offline
        from prysm.tools.mobile.device import MobileDeviceTools

        tools = MobileDeviceTools(container.mobile_service)
        try:
            res = await tools.device_status(args.device_id)
            print(f"Status: {res}")
        except Exception as e:
            print(f"Error: {e} (Device might be offline)")


def main():
    parser = argparse.ArgumentParser(
        prog="prysm", description="A modular, async-first personal AI assistant"
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    subparsers = parser.add_subparsers(dest="command")

    # Subcommands
    subparsers.add_parser("chat", help="Start the interactive development chat")

    audio_parser = subparsers.add_parser("audio", help="Audio utilities")
    audio_subs = audio_parser.add_subparsers(dest="audio_cmd")
    audio_subs.add_parser("devices", help="List audio devices")
    audio_subs.add_parser("test-input", help="Test microphone volume levels")

    stt_parser = subparsers.add_parser("stt", help="STT utilities")
    stt_subs = stt_parser.add_subparsers(dest="stt_cmd")
    stt_subs.add_parser("test", help="Record 5 seconds and transcribe")

    tts_parser = subparsers.add_parser("tts", help="TTS utilities")
    tts_subs = tts_parser.add_subparsers(dest="tts_cmd")
    tts_test = tts_subs.add_parser("test", help="Test TTS synthesis")
    tts_test.add_argument(
        "--text",
        default="Hello, this is a test of the text to speech system.",
        help="Text to synthesize",
    )

    device_parser = subparsers.add_parser("device", help="Mobile device management")
    device_subs = device_parser.add_subparsers(dest="device_cmd")
    device_subs.add_parser("list", help="List paired devices")
    device_subs.add_parser("pair", help="Generate a pairing code")
    device_status_parser = device_subs.add_parser("status", help="Get device status")
    device_status_parser.add_argument("device_id", help="Device ID")
    device_revoke_parser = device_subs.add_parser("revoke", help="Revoke a device")
    device_revoke_parser.add_argument("device_id", help="Device ID")

    args = parser.parse_args()

    try:
        if args.command == "chat":
            asyncio.run(run_chat())
        elif args.command == "audio":
            if args.audio_cmd == "devices":
                list_devices()
            elif args.audio_cmd == "test-input":
                asyncio.run(test_input())
        elif args.command == "stt":
            if args.stt_cmd == "test":
                asyncio.run(test_stt())
        elif args.command == "tts":
            if args.tts_cmd == "test":
                asyncio.run(test_tts(args.text))
        elif args.command == "device":
            asyncio.run(run_device_command(args))
        else:
            asyncio.run(async_main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
