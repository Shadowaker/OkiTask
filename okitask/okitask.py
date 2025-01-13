import sys
import subprocess

import utility.colors as cl
import parser
import task as ts
from errors import TaskStopError

COMMANDS = []

# todo pass print to logging module

def start_task(task: ts.Task):
    """Start a task processes."""

    for x in range(0, task.amount):

        try:
            proc = subprocess.Popen(task.command_list(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            proc = ts.Process(x, f"{task.name}", proc)
            task.add_process(proc)
            proc.change_status(1)
            print(f"Started {proc}...")
        except Exception as e:
            print(f"{cl.BRIGHT_RED}Error: Process {x} of task {task.name} failed.\nReason: {e}")
            stop_task(task)
            task.set_status(3)
            return
    task.set_status(2)


def stop_task(task: ts.Task):
    """Stop a task processes."""

    for proc in task.processes:
        try:
            proc.process.terminate()
            proc.process.wait()
            proc.change_status(0)
        except Exception as e:
            print(f"{cl.BRIGHT_RED}Error: Process {proc} failed to stop.\nReason: {e}")
            raise TaskStopError(f"Can't stop task: {e}")
    task.set_status(0)


def restart_task(task: ts.Task):
    """Restart a task processes."""
    try:
        stop_task(task)
    except TaskStopError:
        # TODO Here think about task recovery
        # A task cannot be stopped only because the main process doesn't have enough privilege
        return
    start_task(task)


def status():
    pass


def startup(tasks: list):
    print(f"{cl.GREEN}Autostarting processes...{cl.BLANK}")

    for task in tasks:
        if task.auto_start:
            start_task(task)

    print(f"{cl.GREEN}Done.{cl.BLANK}")


def main(argv: list):

    try:
        conf = parser.ConfigParser(argv[1])
    except parser.ParseError as e:
        print(f"{cl.BRIGHT_RED}Error:{cl.BLANK} {e}")
        return
    except IndexError:
        print(f"{cl.BRIGHT_RED}Error:{cl.BLANK} File not found")
        return

    tasks = []
    for x in conf.tasks:
        try:
            tasks.append(ts.Task(str(x), **conf.tasks[x]))
        except ts.TaskInitError as e:
            print(f"{cl.BRIGHT_RED}Error:{cl.BLANK} {e}")
            return

    startup(tasks)


if "__main__" == __name__:

    try:
        main(sys.argv)
    except KeyboardInterrupt:
        exit(0)

