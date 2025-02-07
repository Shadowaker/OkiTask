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

def stop():
    global RUNNING

    with RUNNING_MUTEX:
        RUNNING = False


def startup(tasks: list[ts.Task]):
    logging.info(f"Autostarting processes...")

    for task in tasks:
        if task.auto_start:
            task.run()

    logging.info(f"Done.")


def main_loop(tasks: list[ts.Task]):

    logging.debug(f"Starting main loop.")
    startup(tasks)
    while RUNNING:
        for task in tasks:
            task.check_process_running()
            task.restart_failed_processes()

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

    tasks = []
    for x in conf.tasks:
        try:
            definition = ts.TaskDefinition(**conf.tasks[x])
            tasks.append(ts.Task(str(x), definition))
        except ts.TaskInitError as e:
            logging.error(f"Error: {e}")
            return

    try:
        shell = sh.Shell(tasks, stop)
        shell_thread = threading.Thread(target=shell.cmdloop)
        shell_thread.daemon = True
        shell_thread.start()
    except KeyboardInterrupt:
        stop()

    main_loop(tasks)

    logging.debug(f"Exiting main loop.")
    print("Cleaning...")
    for task in tasks:
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


