
class Shell:

    def __init__(self):
        self.commands = {
            "display": self.general, "stop": self.general, "down": self.general, "run": self.general,
            "up": self.general, "ps": self.general, "help": self.help_command, "exit": self.exit
        }

    def parser(self, inp: str):

        args: list[str] = inp.split(" ")
        if not args:
            return None

        try:
            return self.commands[args[0]](args[1:])
        except KeyError:
            return self.error()

    def general(self, args: list):
        pass

    def help_command(self, args: list):
        return """
        run\t[task_name]\t - Run task if not already running\n
        stop\t[task_name]\t - stop task if running\n
        display\t[task_name]\t - see the task state\n
        up\t\t\t - run all tasks not running\n
        down\t\t\t - stop all tasks running\n
        ps\t\t\t - display all tasks running and their state\n
        """

    def error(self):
        return "Command not found, if you need help type 'help'.\nType 'exit' for exiting the shell"

    def exit(self, args: list):
        return False

