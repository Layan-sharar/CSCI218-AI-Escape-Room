
from enum import Enum, auto


class Status(Enum):
    SUCCESS = auto()
    FAILURE = auto()
    RUNNING = auto()


class Node:
    def __init__(self, name="Node"):
        self.name = name
        self.last_status = None

    def tick(self):
        raise NotImplementedError(
            "Each node must implement tick()"
        )


class Sequence(Node):
    def __init__(self, children, name="Sequence"):
        super().__init__(name)
        self.children = children

    def tick(self):
        for child in self.children:
            status = child.tick()

            if status != Status.SUCCESS:
                self.last_status = status
                return status

        self.last_status = Status.SUCCESS
        return Status.SUCCESS


class Selector(Node):
    def __init__(self, children, name="Selector"):
        super().__init__(name)
        self.children = children

    def tick(self):
        for child in self.children:
            status = child.tick()

            if status != Status.FAILURE:
                self.last_status = status
                return status

        self.last_status = Status.FAILURE
        return Status.FAILURE


class Condition(Node):
    def __init__(self, check, name="Condition"):
        super().__init__(name)
        self.check = check

    def tick(self):
        self.last_status = (
            Status.SUCCESS
            if self.check()
            else Status.FAILURE
        )
        return self.last_status


class Action(Node):
    def __init__(self, execute, name="Action"):
        super().__init__(name)
        self.execute = execute

    def tick(self):
        self.last_status = self.execute()

        if not isinstance(self.last_status, Status):
            raise TypeError(
                f"{self.name} must return a Status"
            )

        return self.last_status
