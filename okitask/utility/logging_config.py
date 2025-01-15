from logging import DEBUG, INFO, WARNING, ERROR

LEVELS = {
    "DEBUG": DEBUG,
    "INFO": INFO,
    "WARNING": WARNING,
    "ERROR": ERROR
}

class LoggingConfigError(Exception):
    """Base error class"""


class LoggingConfig:

    def __init__(self, **kwargs):

        self.level = LEVELS.get(kwargs.get("level", "DEBUG"), DEBUG)

    def set_level(self, val: str):
        if val not in LEVELS:
            raise LoggingConfigError(f"Level need to be a string in {LEVELS.keys()}")

        self.level = LEVELS[val]

