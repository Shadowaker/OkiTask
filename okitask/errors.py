

class OkiTaskError(Exception):
    """Base error class"""


class TaskInitError(OkiTaskError):
    """Task object can't be initialized"""


class ParseError(OkiTaskError):
    """General parser error"""

