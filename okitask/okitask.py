import os
import sys
import subprocess
import logging

# utility directory
import utility.colors as cl
from utility import logging_config

# parser.py
import parser

# task.py
import task as ts



TITLE = """
 ██████╗ ██╗  ██╗██╗████████╗ █████╗ ███████╗██╗  ██╗\n
██╔═══██╗██║ ██╔╝██║╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝\n
██║   ██║█████╔╝ ██║   ██║   ███████║███████╗█████╔╝ \n
██║   ██║██╔═██╗ ██║   ██║   ██╔══██║╚════██║██╔═██╗ \n
╚██████╔╝██║  ██╗██║   ██║   ██║  ██║███████║██║  ██╗\n
 ╚═════╝ ╚═╝  ╚═╝╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝\n
"""

COMMANDS = []


def startup(tasks: list[ts.Task]):
    logging.info(f"{cl.GREEN}Autostarting processes...{cl.BLANK}")

    for task in tasks:
        if task.auto_start:
            task.run()

    logging.info(f"{cl.GREEN}Done.{cl.BLANK}")


def main(argv: list):

    # getting configs
    try:
        conf = parser.ConfigParser(argv[1])
        try:
            log_conf = logging_config.LoggingConfig(**conf.log)
        except [NotImplementedError, AttributeError]:
            log_conf = logging_config.LoggingConfig(level="DEBUG")
    except parser.ParseError as e:
        print(f"{cl.BRIGHT_RED}Error:{cl.BLANK} {e}")
        return
    except IndexError:
        print(f"{cl.BRIGHT_RED}Error:{cl.BLANK} File not passed.")
        print(f"{cl.BRIGHT_RED}File required. {cl.BLANK}")
        return

    # setting up logging
    logging.basicConfig(format='[%(levelname)s] %(message)s', level=log_conf.level)

    tasks = []
    for x in conf.tasks:
        try:
            tasks.append(ts.Task(str(x), **conf.tasks[x]))
        except ts.TaskInitError as e:
            logging.error(f"{cl.BRIGHT_RED}Error:{cl.BLANK} {e}")
            return

    startup(tasks)

    logging.debug(f"Starting main loop.")
    try:
        while 1:
            for task in tasks:
                task.check_process_running()
                task.restart_failed_processes()
    except KeyboardInterrupt:
        logging.debug(f"Exiting main loop.")
        for task in tasks:
            task.stop()
        logging.debug(f"Exited main loop.")


if "__main__" == __name__:

    try:
        username = os.environ.get('USER', os.environ.get('USERNAME', "User"))
    except [AttributeError, ValueError, TypeError, OSError]:    # better safe than sorry
        username = "User"

    print("\n", TITLE, "\n")
    print(f"{cl.GREEN} Welcome {username}!", {cl.BLANK})
    main(sys.argv)
    print(f"{cl.BRIGHT_RED} Bye {username}!")

