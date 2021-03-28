import logging
from logging import Logger, handlers
from pathlib import Path

TRACE_LEVEL = 5


def setup() -> None:
    logging.TRACE = TRACE_LEVEL
    logging.addLevelName(TRACE_LEVEL, "TRACE")
    Logger.trace = _monkeypatch_trace

    logging_level = TRACE_LEVEL if True else logging.INFO
    format_string = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    logging_format = logging.Formatter(format_string)

    logging_file = Path("data/logs", "prostotools.log")
    logging_file.parent.mkdir(exist_ok=True)
    file_handler = handlers.TimedRotatingFileHandler(logging_file, when="d", backupCount=7, encoding="utf8")
    file_handler.setFormatter(logging_format)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging_format)

    root_logging = logging.getLogger()
    root_logging.setLevel(logging_level)
    root_logging.addHandler(file_handler)
    root_logging.addHandler(console_handler)

    logging.getLogger("discord").setLevel(logging.WARNING)


def _monkeypatch_trace(self: logging.Logger, msg: str, *args, **kwargs) -> None:
    if self.isEnabledFor(TRACE_LEVEL):
        self._log(TRACE_LEVEL, msg, args, **kwargs)