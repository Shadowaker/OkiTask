

class OkiTaskError(Exception):
    """Base error class"""

# ----------------------------------------------

class TaskInitError(OkiTaskError):
    """Task object can't be initialized"""

class TaskStopError(OkiTaskError):
    """Task can't be stopped"""

class TaskStartError(OkiTaskError):
    """Task can't be started"""

class TaskAlreadyRunning(OkiTaskError):
    """Task is already running"""

class TaskAlreadyStopped(OkiTaskError):
    """Task is already stopped"""

# -----------------------------------------------

class SetTypeError(OkiTaskError):
    """Type passed is not allowed"""

class ParseError(OkiTaskError):
    """General parser error"""
