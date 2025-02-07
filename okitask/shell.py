import cmd

class Shell(cmd.Cmd):
    intro = 'Type help or ? to list commands.\nCTRL+C to exit.\n'
    prompt = '> '

    def __init__(self, tasks, stop):
        super().__init__()
        self.tasks = tasks
        self.stop = stop

    def do_run(self, arg):
        """Start a specified task: start task_name"""
        task = self._get_task(arg)
        if task:
            task.run()

    def do_stop(self, arg):
        """Stop a specified task: stop task_name"""
        task = self._get_task(arg)
        if task:
            task.stop()

    def do_restart(self, arg):
        """Restart a specified task: restart task_name"""
        task = self._get_task(arg)
        if task:
            task.restart()

    def do_status(self, arg: list[str]):
        """Display the status of all tasks"""
        for task in self.tasks:
            task.display_status()

    def do_exit(self, arg: list[str]):
        """Exit the shell and stop the program"""
        self.stop()

    def do_reload(self, arg: list[str]):
        pass

    def do_reload(self, arg):
        'Reload the config file'

    def _get_task(self, name):
        for task in self.tasks:
            if task.name == name:
                return task
        print(f'Task "{name}" not found.')
        return None
