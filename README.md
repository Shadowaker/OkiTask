# Okitask 🚀

### Description 📋
**Okitask** is a job control manager inspired by Supervisor, designed for UNIX-like operating systems. \
It allows users to control multiple processes through a configuration file. 

### Features 🌟

- **Process Management**: Start, monitor, and manage background processes.
- **Flexible Configuration**: Define processes using INI-style configuration files.
- **Advanced Logging**: Record process activities for debugging and monitoring.

### Technologies Used 💻
- **Language**: Python
- **Libraries**: Python std library

### Installation 🔨

1. Clone the repository:
    ```git clone https://github.com/shadowaker/okitask.git```
2. Navigate to the project directory:
    ```cd okitask```
3. Execute with predefined config:
    ```python3 okitask/okitask.py test-example/config.json```


### Configuration ⚙️
Example configuration file (json file):
```
{
    "tasks": {
        "test": {
            "cmd": "curl parrot.live",
            "amount": 5,
            "auto_start": false,
            "auto_restart": "unexpected",
            "expected_outputs":
                [
                    0,
                    2
                ],
            "time_start": 10,
            "max_retries": 1,
            "kill_signal": "SIGINT",
            "time_stop": 1,
            "stdout": "./tst.txt",
            "stderr": "",
            "env": {
            },
            "dir": ".",
            "umask": "0666"
          }
      },
    "log": {
        "level": "INFO"
      }
}
```
## Contributing 💡
Feel free to fork the repository and submit pull requests with improvements or bug fixes.
