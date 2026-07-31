import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def short_log(context, *args):
    if context.get("debug"):
        logger.debug(" ".join(map(str, args)))


def log(context, *args, tag=None, level="info"):
    if not context.get("debug") and level == "debug":
        return

    message = " ".join(map(str, args))

    if tag:
        message = f"[{tag}] {message}"

    if level == "debug":
        logger.debug(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)
    else:
        logger.info(message)
