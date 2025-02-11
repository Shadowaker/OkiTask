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

ALWAYS = "always"
NEVER = "never",
UNEXPECTED = "unexpected"

TASK_DEFINITION_TYPES = {
            "name": str, "cmd": str, "amount": int, "auto_start": bool,
            "auto_restart": str, "expected_output": list, "time_start": int,
            "max_retries": int, "kill_signal": str, "time_stop": int,
            "stdout": str, "stderr": str, "env": dict, "dir": str, "umask": str
        }


class Process:

    def __init__(self, _id: int, name: str, process: Popen):
        self.id = _id
        self.name = name
        self.process = process
        self.status = STOPPED
        self.retried = 0
        self.started_time = time.time()

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
            self.kill_signal = getattr(signal.Signals, self.kill_signal).value
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

        if not 0 <= self.umask <= 0o777:
            raise TaskInitError(f"The passed umask ({self.umask}) is not valid")

        for i, code in enumerate(self.expected_output):
            self.expected_output[i] = int(code)

    def get_command_list(self) -> list[str]:
        return self.cmd.split(" ")

    def get_updated_env(self):
        current_env = os.environ.copy()
        for key in self.env:
            current_env[key] = self.env[key]
        return current_env

    def should_be_restarted(self, other: "TaskDefinition") -> bool:
        return self.cmd != other.cmd or self.stdout != other.stdout or self.stderr != other.stderr or self.env != other.env or self.dir != other.dir != self.umask != other.umask

    def is_expected_exit_code(self, code: int) -> bool:
        if code == 0:
            return True
        if len(self.expected_output) == 0:
            return True
        code = abs(code)
        return code in self.expected_output



class Task:
    """Task base class"""

    def __init__(self, name, definition: TaskDefinition):
        self.name = name
        self.definition = definition
        self.status = "STOPPED"
        self.processes: list[Process] = []

    def __str__(self):
        return f"[TASK]  {cl.CYAN}{self.name}{cl.BLANK}\t\t|\t\t{cl.BACKGROUND_GREEN}{self.status}{cl.BLANK}"

    def _start_process(self, proc_id: int, append: bool = True):
        logging.info(f"Starting a new {self.name} process.")
        if self.definition.stdout != "":
            output_file = open(self.definition.stdout, "a")
            os.chmod(self.definition.stdout, 0o666)
        else:
            output_file = subprocess.PIPE
        if self.definition.stderr != "":
            error_file = open(self.definition.stderr, "a")
            os.chmod(self.definition.stdout, 0o666)
        else:
            error_file = subprocess.PIPE

        try:
            proc = subprocess.Popen(self.definition.get_command_list(), stdout=output_file, stderr=error_file, cwd=self.definition.dir, umask=int(self.definition.umask), env=self.definition.get_updated_env())
            proc = Process(proc_id, f"{self.name}", proc)
            if append:
                self.processes.append(proc)
            proc.change_status(STARTED)
            logging.debug(f"Started {proc}.")
            return proc
        except Exception as e:
            logging.error(f"{cl.BRIGHT_RED}Error: Process {proc_id} of task {self.name} failed.\nReason: {e}")
            return None

    def _stop_process(self, proc: Process, remove: bool = False):
        try:
            proc.change_status(STOPPED)
            proc.process.send_signal(signal.Signals(self.definition.kill_signal))
            proc.process.wait(timeout=self.definition.time_stop)
            logging.info(f"Stopped {proc}.")
        except Exception as e:
            logging.warning(f"Process {proc.id} did not stop in gracefully. Forcing termination...")
            proc.process.kill()
            proc.process.wait()
            proc.change_status(KILLED)
        if remove:
            self.processes.remove(proc)

    def run(self, force: bool = False):
        if self.status != "STOPPED" and not force:
            raise TaskAlreadyRunning("This task is already running")

        logging.info(f"Starting {self.name}")
        for x in range(len(self.processes), self.definition.amount):
            if self._start_process(x) is None:
                try:
                    self.stop()
                except TaskStopError:
                    pass
                return False

        logging.info(f"{self.name} started.")
        self.status = "ACTIVE"

    def stop(self):
        logging.info(f"Stopping {self.name}")
        for proc in self.processes:
            self._stop_process(proc)

        logging.info(f"{self.name} stopped.")
        self.status = "STOPPED"

    def restart(self):
        logging.info(f"Restarting... {self.name}")
        try:
            self.stop()
        except TaskStopError:
            pass

        self.processes.clear()
        self.run()

    def reconcile(self):
        logging.info(f"Reconciling... {self.name}")
        if len(self.processes) > self.definition.amount:
            logging.debug(f"{self.name} has more processes than the amount defined in the config file. Removing extra processes.")
            for proc in self.processes[self.definition.amount:]:
                self._stop_process(proc, True)
        elif len(self.processes) < self.definition.amount and self.definition.auto_start:
            logging.debug(f"{self.name} has less processes than the amount defined in the config file. Adding extra processes.")
            self.run(True)


    def check_process_running(self):
        logging.debug(f"[{self.name}] Starting check loop...")

        for proc in self.processes:
            if proc.process.poll() is None:
                if (time.time() - proc.started_time) >= self.definition.time_start and proc.status == STARTED:
                    proc.change_status(ACTIVE)
                continue
            if proc.status != STOPPED:
                proc.change_status(EXITED)

        logging.debug(f"[{self.name}] Ended check loop.")

    def restart_failed_processes(self):
        logging.debug(f"[{self.name}] Starting restart loop...")
        for i, proc in enumerate(self.processes):
            if proc.status == EXITED and self.definition.auto_restart in [ALWAYS, UNEXPECTED]:
                return_code = proc.process.returncode
                expected = self.definition.is_expected_exit_code(return_code)
                if (not expected and self.definition.auto_restart == UNEXPECTED) or self.definition.auto_restart == ALWAYS:
                    new_proc = self._start_process(proc.id, False)
                    new_proc.set_retried(proc.retried + 1)
                    self.processes[i] = new_proc
                    del proc
        logging.debug(f"[{self.name}] Ended restart loop.")

    def display_status(self):

        print(self)
        for proc in self.processes:
            exit_code = f"exited with code: {abs(proc.process.returncode)}" if proc.process.returncode is not None else ""
            print(f"  > {cl.MAGENTA}{proc.id}{cl.BLANK} ({proc.process.pid}) {cl.BACKGROUND_GREEN}{STATUS[proc.status]}{cl.BLANK}\t| {exit_code}")
