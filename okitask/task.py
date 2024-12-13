import signal
import os

from subprocess import Popen

from errors import TaskInitError

STATUS = {
    0: "STOPPED",
    1: "STARTED",
    2: "ACTIVE",
    3: "KILLED"
}


class Process:

    def __init__(self, _id: int, name: str, process: Popen):
        self.id = _id
        self.name = name
        self.process = process
        self.status = 0

    def __str__(self):
        return f"({self.process.pid}) {self.name}_{self.id} | {STATUS[self.status]}"

    def change_status(self, status: int):
        self.status = status

class TaskDescription:

    def __init__(self, name, **kwargs):
        self.name = name
        self.status = 0
        self.exit_code = None
        self.processes: [Process] = []

        try:
            self.cmd, self.amount = kwargs["cmd"], kwargs["amount"]
            self.auto_start = kwargs.get("auto_start", True)
            self.auto_restart = kwargs.get("auto_restart", "never")
            self.expected_output = kwargs.get("expected_outputs", [])
            self.time_start, self.max_retries = kwargs.get("time_start", 1), kwargs.get("max_retries", 1)
            self.kill_signal, self.time_stop = kwargs.get("kill_signal", "SIGKILL"), kwargs.get("time_stop", 1)
            self.stdout, self.stderr, = kwargs.get("stdout", ""), kwargs.get("stderr", "")
            self.env = kwargs.get("env", [])
            self.dir, self.umask = kwargs.get("dir", "."), kwargs.get("umask", "0666")
        except KeyError as e:
            raise TaskInitError("Can't init task object")

        d = {
            "name": str, "cmd": str, "amount": int, "auto_start": bool,
            "auto_restart": str, "expected_output": list, "time_start": int,
            "max_retries": int, "kill_signal": str, "time_stop": int,
            "stdout": str, "stderr": str, "env": dict, "dir": str, "umask": str
        }

        # check config types
        for x in dir(self):
            try:
                if not isinstance(getattr(self, x), d[x]):
                    raise TaskInitError(
                        f"Config passed not valid!\n"
                        f"{x} needs to be {d[x]}"
                    )
            except KeyError:
                continue

        try:

            self.kill_signal = getattr(signal.Signals, self.kill_signal)
        except AttributeError:
            raise TaskInitError(f"Kill signal needs to be a valid signal, not {self.kill_signal}")

        if self.auto_restart not in ["never", "always", "unexpected"]:
            raise TaskInitError(f"Auto Restart is not valid, needs to be 'never', 'always' or 'unexpected'")

        if self.dir == ".":
            self.home = os.getcwd()
        else:
            try:
                os.chdir(self.dir)
            except OSError:
                raise TaskInitError(f"The passed dir ({self.dir}) config is not valid")

        try:
            self.umask = int(self.umask, 8)
        except ValueError:
            raise TaskInitError(f"The passed umask ({self.umask}) is not an octal")
        try:
            os.umask(self.umask)
            # TODO: Change validation here, we're changing the process umask not checking if that's a valid one
        except OSError:
            raise TaskInitError(f"The passed umask ({self.umask}) is not valid")

        for x in self.env:
            os.putenv(str(x), self.env[x])

class Task:
    """Task base class"""

    def __init__(self, name, **kwargs):
        self.name = name
        self.status = 0
        self.exit_code = None
        self.processes: [Process] = []

        try:
            self.cmd, self.amount = kwargs["cmd"], kwargs["amount"]
            self.auto_start = kwargs.get("auto_start", True)
            self.auto_restart = kwargs.get("auto_restart", "never")
            self.expected_output = kwargs.get("expected_outputs", [])
            self.time_start, self.max_retries = kwargs.get("time_start", 1), kwargs.get("max_retries", 1)
            self.kill_signal, self.time_stop = kwargs.get("kill_signal", "SIGKILL"), kwargs.get("time_stop", 1)
            self.stdout, self.stderr, = kwargs.get("stduot", ""), kwargs.get("stderr", "")
            self.env = kwargs.get("env", [])
            self.dir, self.umask = kwargs.get("dir", "."), kwargs.get("umask", "0666")
        except KeyError as e:
            raise TaskInitError("Can't init task object")

        d = {
            "name": str, "cmd": str, "amount": int, "auto_start": bool,
            "auto_restart": str, "expected_output": list, "time_start": int,
            "max_retries": int, "kill_signal": str, "time_stop": int,
            "stdout": str, "stderr": str, "env": dict, "dir": str, "umask": str
        }

        # check config types
        for x in dir(self):
            try:
                if not isinstance(getattr(self, x), d[x]):
                    raise TaskInitError(
                        f"Config passed not valid!\n"
                        f"{x} needs to be {d[x]}"
                    )
            except KeyError:
                continue

        try:

            self.kill_signal = getattr(signal.Signals, self.kill_signal)
        except AttributeError:
            raise TaskInitError(f"Kill signal needs to be a valid signal, not {self.kill_signal}")

        if self.auto_restart not in ["never", "always", "unexpected"]:
            raise TaskInitError(f"Auto Restart is not valid, needs to be 'never', 'always' or 'unexpected'")

        if self.dir == ".":
            self.home = os.getcwd()
        else:
            try:
                os.chdir(self.dir)
            except OSError:
                raise TaskInitError(f"The passed dir ({self.dir}) config is not valid")

        try:
            self.umask = int(self.umask, 8)
        except ValueError:
            raise TaskInitError(f"The passed umask ({self.umask}) is not an octal")
        try:
            os.umask(self.umask)
        except OSError:
            raise TaskInitError(f"The passed umask ({self.umask}) is not valid")

        for x in self.env:
            os.putenv(str(x), self.env[x])

    def __str__(self):
        return f"{self.name}\t|\t{STATUS[self.status]}\t"

    def command_list(self):
        return [self.cmd]

    def add_process(self, proc: Process):
        self.processes.append(proc)

    def set_status(self, status: int):
        self.status = status


class TaskHandler:
    def __init__(self):
        self.tasks = []

    def reload(self, tasks: Task):
        pass
