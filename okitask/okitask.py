import sys
import subprocess

import utility.colors as cl
import parser
import task as ts

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


def restart_task(task: ts.Task):
    """Restart a task processes."""
    task.set_status(0)
    stop_task(task)
    start_task(task)


def status():
    pass


def main(argv: list):

    try:
        conf = parser.ConfigParser(argv[0])
    except parser.ParseError as e:
        print(f"{cl.BRIGHT_RED}Error:{cl.BLANK} {e}")
        return

    tasks = []
    for x in conf.tasks:
        try:
            tasks.append(ts.Task(x["name"], **x))
        except ts.TaskInitError as e:
            print(f"{cl.BRIGHT_RED}Error:{cl.BLANK} {e}")
            return

    print(f"{cl.GREEN}Starting processes...{cl.BLANK}")

main(*sys.argv)
