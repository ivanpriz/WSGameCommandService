import logging

from app.config import Config


class CustomFormatter(logging.Formatter):
    def format(self, record):
        # сохраняем исходный формат
        original_format = self._style._fmt

        logger_format_debug = Config.LOGGER_FORMAT_DEBUG if Config.LOGGER_FORMAT_DEBUG else original_format
        logger_format_info = Config.LOGGER_FORMAT_INFO if Config.LOGGER_FORMAT_INFO else original_format

        if record.levelno == logging.DEBUG:
            self._style._fmt = logger_format_debug

        elif record.levelno == logging.INFO:
            self._style._fmt = logger_format_info

        result = super().format(record)

        # возвращаем исходный формат
        self._style._fmt = original_format

        return result


def get_logger(name, logger_level=None):
    logger = logging.getLogger(name)

    if not logger_level:
        logger_level = logging.DEBUG

    logger.setLevel(logger_level)

    formatter = CustomFormatter()

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    # чтобы избежать дубликатов логов
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(handler)

    return logger
