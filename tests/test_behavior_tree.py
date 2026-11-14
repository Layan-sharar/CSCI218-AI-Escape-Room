
from ai.behavior_tree import (
    Status,
    Sequence,
    Selector,
    Condition,
    Action
)


def test_sequence():
    tree = Sequence([
        Condition(lambda: True, "Check 1"),
        Condition(lambda: True, "Check 2")
    ])

    assert tree.tick() == Status.SUCCESS


def test_sequence_running():
    tree = Sequence([
        Condition(lambda: True),
        Action(lambda: Status.RUNNING)
    ])

    assert tree.tick() == Status.RUNNING


def test_selector():
    tree = Selector([
        Condition(lambda: False),
        Action(lambda: Status.SUCCESS)
    ])

    assert tree.tick() == Status.SUCCESS


def test_selector_failure():
    tree = Selector([
        Condition(lambda: False),
        Condition(lambda: False)
    ])

    assert tree.tick() == Status.FAILURE


def test_action_validation():
    tree = Action(lambda: True)

    try:
        tree.tick()
        assert False, "Expected TypeError"
    except TypeError:
        pass
