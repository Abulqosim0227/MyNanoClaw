import asyncio
import logging
import sys

from claw.config import Config, ConfigError
from claw.telegram.bot import create_bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("claw")


def main() -> None:
    try:
        config = Config.load()
    except ConfigError as e:
        logger.error("Config error: %s", e)
        sys.exit(1)

    bot, dp = create_bot(config)

    logger.info("Claw is starting...")

    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
