import hashlib
import logging
import re
import sys

from settings import settings
from loguru import logger


def get_str_hash(filename: str):
    with open(filename, 'rb', buffering=0) as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


# Output as JSON
serialize = False
if settings.log_level == "production":
    serialize = True


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


# LOG_LEVELs
# 0: INFO
# 1: DEBUG
# 2: DEBUG with TRACE
# 3: TRACE with all TRACES

# Start logger
if settings.log_level == "3":
    logging.basicConfig(handlers=[InterceptHandler()], level=0)
    logger.warning("logger level set to DEBUG with full TRACING")

elif settings.log_level == "2":
    logger.info("logger level set to DEBUG with TRACE")

elif settings.log_level == "1":
    logger.remove()
    logger.info("logger level set to DEBUG")
    logger.add(
        sys.stdout,
        colorize=True,
        level="DEBUG",
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        backtrace=True,
        serialize=serialize,
        diagnose=False,
    )

else:
    logger.remove()
    logger.info("logger level set to INFO")
    logger.add(
        sys.stdout,
        colorize=True,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        backtrace=True,
        serialize=serialize,
        diagnose=False,
    )


def extract_text_between_tags(html_string, tag):
    """
    Extracts text between specified tags in an HTML string.

    Args:
        html_string: The HTML string to search within.
        tag: The tag name (e.g., 'p', 'div', 'span').

    Returns:
        A list of strings containing the text found between the tags.
        Returns an empty list if no matching tags are found.
    """
    regex = r"<{tag}.*?>(.*?)</{tag}>".format(tag=tag)
    matches = re.findall(regex, html_string)
    return matches
