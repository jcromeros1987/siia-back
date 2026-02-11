import logging

logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s: %(message)s", datefmt="%d/%b/%Y %H:%M:%S"
)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.setLevel(logging.DEBUG)


class ContextFilter(logging.Filter):
    def filter(self, record):
        record.user_id = getattr(record, "user_id", "-")
        record.action = getattr(record, "action", "-")
        record.path = getattr(record, "path", "-")
        record.method = getattr(record, "method", "-")
        return True
