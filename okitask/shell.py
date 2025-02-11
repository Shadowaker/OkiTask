import cmd
from errors import TaskAlreadyRunning


class Shell(cmd.Cmd):
    intro = 'Type help or ? to list commands.\nCTRL+C to exit.\n'
    prompt = '> '

    def __init__(self, tasks, stop, reload, should_reload):
        super().__init__()
        self.tasks = tasks
        self.stop = stop
        self.reload = reload
        self.should_reload = should_reload

    def do_run(self, arg: list[str]):
        """Start a specified task: start task_name"""

        if self.should_reload():
            return
        task = self._get_task(arg)
        if task:
            try:
                task.run()
            except TaskAlreadyRunning:
                print(f"{task.name} already running.")

    def do_stop(self, arg: list[str]):
        """Stop a specified task: stop task_name"""

        if self.should_reload():
            return
        task = self._get_task(arg)
        if task:
            task.stop()

    def do_restart(self, arg: list[str]):
        """Restart a specified task: restart task_name"""

        if self.should_reload():
            return
        task = self._get_task(arg)
        if task:
            task.restart()

    def do_status(self, arg: list[str]):
        """Display the status of all tasks"""

        if self.should_reload():
            return
        for task in self.tasks:
            task.display_status()

    def do_ps(self, arg: list[str]):
        """Display the status of all tasks"""
        self.do_status(arg)

    def do_exit(self, arg: list[str]):
        """Exit the shell and stop the program"""

        if self.should_reload():
            return
        self.stop()

    def do_reload(self, arg: list[str]):
        """Reload the config file"""

        if self.should_reload():
            return
        self.reload()
        pass


    def _get_task(self, name):

        for task in self.tasks:
            if task.name == name:
                return task
        print(f'Task "{name}" not found.')
        return None
