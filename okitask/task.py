from errors import TaskInitError


class Task:
    """Task base class"""

    def __init__(self, name, **kwargs):

        self.name = name

        try:
            self.cmd, self.amount, self.auto_start = kwargs["cmd"], kwargs["amount"], kwargs["auto_start"]
            self.auto_restart, self.expected_output = kwargs["auto_restart"], kwargs["expected_output"]
            self.time_start, self.max_retries = kwargs["time_start"], kwargs["max_retries"]
            self.kill_signal, self.time_stop = kwargs["signal"], kwargs["time_stop"]
            self.stdout, self.stderr, self.env = kwargs["stdout"], kwargs["stderr"], kwargs["env"]
            self.dir, self.umask = kwargs["dir"], kwargs["umask"]
        except KeyError:
            raise TaskInitError("Can't init task object")


