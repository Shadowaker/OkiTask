import json

from errors import ParseError

class Parser:
    """Basic config parser"""

    def __init__(self, path):
        try:
            with open(path, "r") as f:
                reading = f.read()
        except IOError as e:
            raise ParseError(f"Invalid config file passed: {e}")

        self.raw = reading

        try:
            self.json = json.loads(self.raw)
        except (json.JSONDecodeError, ValueError) as e:
            raise ParseError(f"Invalid or corrupted Json: {e}")

        self.attrs = []
        for k, v in self.json.items():
            setattr(self, k, v)
            self.attrs.append(k)

    def __aslist__(self):
        return [x for x in dir(self)]

    def __iter__(self):
        return iter(self.__aslist__())

    def to_dict(self):
        return {x: getattr(self, x) for x in dir(self)}

    def validate(self):
        return True

