import signal
import os
import subprocess
import logging
import time

from subprocess import Popen

from errors import TaskInitError, SetTypeError, TaskStopError, TaskAlreadyRunning, TaskAlreadyStopped
import utility.colors as cl

STOPPED = 0
STARTED = 1
ACTIVE = 2
KILLED = 3
EXITED = 4

STATUS = {
    0: "STOPPED",
    1: "STARTED",
    2: "ACTIVE",
    3: "KILLED",
    4: "EXITED"
}


class Process:

    def __init__(self, _id: int, name: str, process: Popen):
        self.id = _id
        self.name = name
        self.process = process
        self.status = STOPPED
        self.retried = 0

    def __str__(self):
        return f"({self.process.pid}) {self.name}_{self.id} | {STATUS[self.status]}"

    def change_status(self, status: int):
        if isinstance(status, int):
            self.status = status
        else:
            raise SetTypeError("Value must be an int.")

    def set_retried(self, val: int):
        if not isinstance(val, int):
            raise SetTypeError("Value must be an int.")
        self.retried = val

TASK_DEFINITION_TYPES = {
            "name": str, "cmd": str, "amount": int, "auto_start": bool,
            "auto_restart": str, "expected_output": list, "time_start": int,
            "max_retries": int, "kill_signal": str, "time_stop": int,
            "stdout": str, "stderr": str, "env": dict, "dir": str, "umask": str
        }

class TaskDefinition:

    def __init__(self, **kwargs):
        try:
            self.cmd, self.amount = kwargs["cmd"], kwargs["amount"]
            self.auto_start = kwargs.get("auto_start", True)
            self.auto_restart = kwargs.get("auto_restart", "never")
            self.expected_output = kwargs.get("expected_outputs", [])
            self.time_start, self.max_retries = kwargs.get("time_start", 0), kwargs.get("max_retries", 1)
            self.kill_signal, self.time_stop = kwargs.get("kill_signal", "SIGKILL"), kwargs.get("time_stop", 1)
            self.stdout, self.stderr, = kwargs.get("stdout", ""), kwargs.get("stderr", "")
            self.env = kwargs.get("env", [])
            self.dir, self.umask = kwargs.get("dir", "."), kwargs.get("umask", "0666")
        except KeyError:
            raise TaskInitError("Can't init task object")

        self._validate_types()
        self._validate_values()

    def _validate_types(self):
        for x in dir(self):
            try:
                if not isinstance(getattr(self, x), TASK_DEFINITION_TYPES[x]):
                    raise TaskInitError(
                        f"Config passed not valid!\n"
                        f"{x} needs to be {TASK_DEFINITION_TYPES[x]}"
                    )
            except KeyError:
                continue

    def _validate_values(self):
        try:
            self.kill_signal = getattr(signal.Signals, self.kill_signal)
        except AttributeError:
            raise TaskInitError(f"Kill signal needs to be a valid signal, not {self.kill_signal}")

        if self.auto_restart not in ["never", "always", "unexpected"]:
            raise TaskInitError(f"Auto Restart is not valid, needs to be 'never', 'always' or 'unexpected'")

        if self.dir == ".":
            self.dir = os.getcwd()
        elif os.path.isdir(self.dir) and os.access(path=self.dir, mode=os.X_OK):
                raise TaskInitError(f"The passed dir ({self.dir}) config is not valid")

        try:
            self.umask = int(self.umask, 8)
        except ValueError:
            raise TaskInitError(f"The passed umask ({self.umask}) is not an octal")

        if 0 <= self.umask <= 0o777:
            raise TaskInitError(f"The passed umask ({self.umask}) is not valid")

    def get_command_list(self) -> list[str]:
        return self.cmd.split(" ")



class Task:
    """Task base class"""

    def __init__(self, name, definition: TaskDefinition):
        self.name = name
        self.definition = definition
        self.status = "STOPPED"
        self.processes: list[Process] = []
        self.started_time = 0

    def __str__(self):
        return f"[TASK]  {cl.CYAN}{self.name}{cl.BLANK}\t|\t{cl.BACKGROUND_GREEN}{self.status}{cl.BLANK}"

    def add_process(self, proc: Process):
        self.processes.append(proc)

    def set_status(self, status: int):
        if isinstance(status, int):
            self.status = status
        else:
            raise SetTypeError("Value must be an int.")

    def run(self):
        if self.status != "STOPPED":
            raise TaskAlreadyRunning("eheh")

        logging.info(f"Starting {self.name}")
        for x in range(len(self.processes), self.definition.amount):

            if self.definition.stdout != "":
                f = open(self.definition.stdout, "a")
                os.chmod(self.definition.stdout, 0o666) # this is here because the file are created by default without permission
            else:
                f = subprocess.PIPE
            if self.definition.stderr != "":
                e = open(self.definition.stderr, "a")
                os.chmod(self.definition.stdout, 0o666)
            else:
                e = subprocess.PIPE

            for l in self.definition.env:
                os.putenv(str(l), self.definition.env[l])

            try:
                proc = subprocess.Popen(self.definition.get_command_list(), stdout=f, stderr=e)
                proc = Process(x, f"{self.name}", proc)
                self.processes.append(proc)
                proc.change_status(STARTED)
                logging.debug(f"Started {proc}.")
            except Exception as e:
                logging.error(f"{cl.BRIGHT_RED}Error: Process {x} of task {self.name} failed.\nReason: {e}")
                try:
                    self.stop()
                except TaskStopError:
                    pass
                return False
        self.started_time = time.time()

        logging.info(f"{self.name} started.")
        self.status = "ACTIVE"

    def stop(self):
        logging.info(f"Stopping {self.name}")
        for proc in self.processes:
            try:
                proc.process.terminate()
                proc.process.wait()
                proc.change_status(STOPPED)
                logging.debug(f"Stopped {proc}.")
            except subprocess.TimeoutExpired:
                logging.warning(f"Process {proc.id} did not stop in time. Forcing termination...")
                proc.process.kill()
                proc.process.wait()
                proc.change_status(KILLED)
            except Exception as e:
                logging.error(f"Error: Process {proc} failed to stop.\nReason: {e}")
                raise TaskStopError(f"Can't stop task: {e}")

        logging.info(f"{self.name} stopped.")
        self.status = "STOPPED"

    def restart(self):
        logging.info(f"Restarting... {self.name}")
        try:
            self.stop()
        except TaskStopError:
            return

        self.run()

    def check_process_running(self):
        logging.debug(f"[{self.name}] Starting check loop...")

        for proc in self.processes:
            if proc.process.poll() is None:
                if (time.time() - self.started_time) >= self.time_start:
                    proc.change_status(ACTIVE)
                continue
            proc.change_status(EXITED)
        logging.debug(f"[{self.name}] Ended check loop.")

    def restart_failed_processes(self):

        logging.debug(f"[{self.name}] Starting restart loop...")
        for i, proc in enumerate(self.processes):
            if proc.status == EXITED:
                if proc.process.returncode != 0: # TODO and filter by expected outputs
                    if self.max_retries > proc.retried:
                        new_proc = subprocess.Popen(
                            self.command_list(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True
                        )
                        new_proc = Process(proc.id, f"{self.name}", new_proc)
                        new_proc.set_retried(proc.retried + 1)
                        self.processes[i] = new_proc
                        del proc
        logging.debug(f"[{self.name}] Ended restart loop.")

    def display_status(self):

        print(self)

        for proc in self.processes:
            exit_code = f"exited with code: {proc.process.returncode}" if proc.process.returncode is not None else ""
            print(f"  > {cl.MAGENTA}{proc.id}{cl.BLANK} {cl.BACKGROUND_GREEN}{STATUS[proc.status]}{cl.BLANK} | {exit_code}")
