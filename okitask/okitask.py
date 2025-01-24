import os
import sys
import logging

# utility directory
import utility.colors as cl
from utility.get_next_line import get_next_line as gnl
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


def startup(tasks: list[ts.Task]):
    logging.info(f"{cl.GREEN}Autostarting processes...{cl.BLANK}")

    for task in tasks:
        if task.auto_start:
            task.run()

    logging.info(f"{cl.GREEN}Done.{cl.BLANK}")


def main_loop(tasks: list[ts.Task], pipe_in):
    logging.debug(f"Starting main loop.")
    try:
        while 1:
            msg = gnl(pipe_in)
            if msg.decode() == "exit":
                raise KeyboardInterrupt("easter")

            for task in tasks:
                task.check_process_running()
                task.restart_failed_processes()
    except KeyboardInterrupt:
        print("")
        logging.debug(f"Exiting main loop.")
        for task in tasks:
            task.stop()
        logging.debug(f"Exited main loop.")


def shell_loop(tasks: list[ts.Task], loop_pid, pipe_out):

    shell = sh.Shell()
    while 1:
        try:
            inp = input("> ")
            res = shell.parser(inp)
            if isinstance(res, str):
                print(res)
            else:
                if res is False:
                    raise KeyboardInterrupt("HELLO")
        except KeyboardInterrupt:
            print(f"\n{cl.YELLOW}Exiting...{cl.BLANK}", end="")
            os.write(pipe_out, b"exit\n")
            os.wait()
            break


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
        print(f"{cl.BRIGHT_RED}Error:{cl.BLANK} File not passed.{cl.BLANK}")
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

    pipe_in, pipe_out = os.pipe()
    process_id = os.fork()
    if process_id == 0:
        os.close(pipe_out)          # main_loop close write pipe (maybe I should keep it open)
        main_loop(tasks, pipe_in)
        os.close(pipe_in)
    else:
        os.close(pipe_in)           # shell close write pipe (maybe I should keep it open)
        shell_loop(tasks, process_id, pipe_out)
        os.close(pipe_out)
        exit(0)


if "__main__" == __name__:

    try:
        username = os.environ.get('USER', os.environ.get('USERNAME', "User"))
    except [AttributeError, ValueError, TypeError, OSError]:    # better safe than sorry
        username = "Monkey"

    print("\n", TITLE,)
    print(f"{cl.GREEN}Welcome {username}!{cl.BLANK}")
    main(sys.argv)
    print(f"{cl.BRIGHT_RED}Bye {username}!")


