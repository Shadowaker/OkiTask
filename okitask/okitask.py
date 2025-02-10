# stdlib
import os
import sys
import logging
import threading

# utility directory
import utility.colors as cl
from utility import logging_config

# parser.py
import parser

# task.py
import task as ts

# shell.py
import shell as sh


TITLE = """
 ██████╗ ██╗  ██╗██╗████████╗ █████╗ ███████╗██╗  ██╗
██╔═══██╗██║ ██╔╝██║╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝
██║   ██║█████╔╝ ██║   ██║   ███████║███████╗█████╔╝
██║   ██║██╔═██╗ ██║   ██║   ██╔══██║╚════██║██╔═██╗
╚██████╔╝██║  ██╗██║   ██║   ██║  ██║███████║██║  ██╗
 ╚═════╝ ╚═╝  ╚═╝╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
"""
RUNNING = True
RUNNING_MUTEX = threading.Lock()

SHOULD_RELOAD = False
SHOULD_RELOAD_MUTEX = threading.Lock()

TASKS = []

def stop():
    global RUNNING

    with RUNNING_MUTEX:
        RUNNING = False

def execute_reload(b: bool = True):
    global SHOULD_RELOAD

    with SHOULD_RELOAD_MUTEX:
        SHOULD_RELOAD = b

def should_reload():
    global SHOULD_RELOAD

    with SHOULD_RELOAD_MUTEX:
        return SHOULD_RELOAD


def startup():
    logging.info(f"Autostarting processes...")

    for task in TASKS:
        if task.definition.auto_start:
            task.run()

    logging.info(f"Done.")


def main_loop():

    logging.debug(f"Starting main loop.")
    startup()
    while RUNNING:
        if should_reload():
            reload()

        for task in TASKS:
            task.check_process_running()
            task.restart_failed_processes()

def reload():
    logging.info("Reloading config file")
    conf = load_config(sys.argv[1])
    task_definitions = {}

    for key in conf.tasks:
        try:
            definition = ts.TaskDefinition(**conf.tasks[key])
            task_definitions[key] = definition
        except ts.TaskInitError as e:
            logging.error(f"Error while reloading config: {e}")
            logging.error("Keeping the old config file. Fix the syntax errors to reload.")
            return

    for task in TASKS:
        if task.name not in task_definitions:
            logging.info(f"Task {task.name} not found in the new config file. Stopping...")
            task.stop()
            TASKS.remove(task)
            continue

        old_definition = task.definition
        task.definition = task_definitions[task.name]
        if task.definition.should_be_restarted(old_definition):
            logging.info(f"Task {task.name} definition changed parameters that are not hot-reloadable. Restarting...")
            task.restart()
            continue

        task.reconcile()

    logging.info("Config file reloaded")



def load_config(config_name: str):

    try:
        conf = parser.ConfigParser(config_name)
    except parser.ParseError as e:
        print(f"{cl.BRIGHT_RED}Error:{cl.BLANK} {e}")
        return None
    except IndexError:
        print(f"{cl.BRIGHT_RED}Error:{cl.BLANK} File not passed.{cl.BLANK}")
        print(f"{cl.BRIGHT_RED}File required. {cl.BLANK}")
        return None

    try:
        log_conf = logging_config.LoggingConfig(**conf.log)
    except [NotImplementedError, AttributeError]:
        log_conf = logging_config.LoggingConfig(level="DEBUG")

    # setting up logging
    logging.basicConfig(
        #filename="log.logs",
        #filemode='w',
        format='[%(levelname)s] %(message)s',
        level=log_conf.level,
    )
    return conf

def main(argv: list):

    conf = load_config(argv[1])

    for x in conf.tasks:
        try:
            definition = ts.TaskDefinition(**conf.tasks[x])
            TASKS.append(ts.Task(str(x), definition))
        except ts.TaskInitError as e:
            logging.error(f"Error: {e}")
            return

    try:
        shell = sh.Shell(TASKS, stop, reload, should_reload)
        shell_thread = threading.Thread(target=shell.cmdloop)
        shell_thread.daemon = True
        shell_thread.start()
    except KeyboardInterrupt:
        stop()

    main_loop()

    logging.debug(f"Exiting main loop.")
    print("Cleaning...")
    for task in TASKS:
        task.stop()
    logging.debug(f"Exited main loop.")


if "__main__" == __name__:

    try:
        username = os.environ.get('USER', os.environ.get('USERNAME', "User"))
    except [AttributeError, ValueError, TypeError, OSError]:    # better safe than sorry
        username = "Monkey"

    print("\n", TITLE,)
    print(f"{cl.GREEN}Welcome {username}!{cl.BLANK}")
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        pass
    print(f"{cl.BRIGHT_RED}Bye {username}!")


