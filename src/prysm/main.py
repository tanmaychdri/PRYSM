import asyncio
import logging
import sys

from prysm.core.assistant import PrysmAssistant


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
    
    assistant = PrysmAssistant()
    
    try:
        await assistant.run()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")

import argparse

def main():
    parser = argparse.ArgumentParser(
        prog="prysm",
        description="A modular, async-first personal AI assistant"
    )
    parser.add_argument(
        "--version", 
        action="version", 
        version="%(prog)s 0.1.0"
    )
    args = parser.parse_args()
    
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
