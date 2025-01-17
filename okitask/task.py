import signal
import os
import subprocess
import logging

from subprocess import Popen

from errors import TaskInitError, SetTypeError, TaskStopError
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

class Task:
    """Task base class"""

    def __init__(self, name, **kwargs):
        self.name = name
        self.status = 0
        self.processes: list[Process] = []

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

    def command_list(self) -> list:
        return self.cmd.split(" ")

    def add_process(self, proc: Process):
        self.processes.append(proc)

    def set_status(self, status: int):
        if isinstance(status, int):
            self.status = status
        else:
            raise SetTypeError("Value must be an int.")

    def run(self):

        logging.info(f"Starting {self.name}")
        for x in range(0, self.amount):

            try:
                proc = subprocess.Popen(self.command_list(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
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
                return

        logging.info(f"{cl.GREEN}{self.name} started.{cl.BLANK}")
        self.status = "ACTIVE"

    def stop(self):
        logging.info(f"{cl.YELLOW}Stopping {self.name} {cl.BLANK}")
        for proc in self.processes:
            try:
                proc.process.terminate()
                proc.process.wait()
                proc.change_status(STOPPED)
                logging.debug(f"Stopped {proc}.")
            except Exception as e:
                logging.error(f"{cl.BRIGHT_RED}Error: Process {proc} failed to stop.\nReason: {e}")
                raise TaskStopError(f"Can't stop task: {e}")

        logging.info(f"{cl.YELLOW}{self.name} stopped. {cl.BLANK}")
        self.status = "STOPPED"

    def restart(self):
        logging.info(f"{cl.YELLOW}Restarting... {self.name} {cl.BLANK}")
        try:
            self.stop()
        except TaskStopError:
            # TODO Here think about task recovery
            # A task cannot be stopped only because the main process doesn't have enough privilege (NOT sure)
            return

        self.run()

    def check_process_running(self):
        logging.debug(f"[{self.name}] Starting check loop...")

        for proc in self.processes:
            if proc.process.poll() is None:
                continue
            proc.change_status(EXITED)
        logging.debug(f"[{self.name}] Ended check loop.")

    def restart_failed_processes(self):

        logging.debug(f"[{self.name}] Starting restart loop...")
        for i, proc in enumerate(self.processes):
            if proc.status == EXITED:
                if proc.process.returncode < 0:
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
        for proc in self.processes:
            print(proc)

