import argparse
import asyncio
import logging
import sys

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
    assistant = container.assistant

    try:
        await assistant.run()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")


async def run_chat():
    setup_logging()
    container = ApplicationContainer()
    assistant = container.assistant

    # Start the assistant background lifecycle
    task = asyncio.create_task(assistant.run())

    # Wait for startup
    await asyncio.sleep(0.5)

    print("\nPRYSM Development Console")
    print("Type 'exit' to quit.\n")

    try:
        while True:
            # simple blocking input for dev cli
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
        await asyncio.sleep(0.2)  # Allow cleanup
        task.cancel()


def main():
    parser = argparse.ArgumentParser(
        prog="prysm", description="A modular, async-first personal AI assistant"
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("chat", help="Start the interactive development chat")

    args = parser.parse_args()

    try:
        if args.command == "chat":
            asyncio.run(run_chat())
        else:
            asyncio.run(async_main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
