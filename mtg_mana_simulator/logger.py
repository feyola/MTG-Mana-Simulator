import sys
from loguru import logger

logger.remove()


# Configure exception handling
def format_record(record):
    format_string = "<white>{time:YYYY-MM-DD HH:mm:ss}</white>" \
                    " | <level>{level: <8}</level>" \
                    " | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>" \
                    " - <white><b>{message}</b></white>\n"

    if record["exception"]:
        format_string += "\n{exception}"
    return format_string


logger.add(
    # Ensure Unicode output on Windows
    sink=sys.stdout,
    format=format_record,
    colorize=True,
    backtrace=True,
    diagnose=True,
    catch=True,
    level="DEBUG",
)

logger = logger.opt(colors=True)