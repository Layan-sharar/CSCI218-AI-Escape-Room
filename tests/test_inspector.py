import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from ai.agent_controller import AgentController
from ai.behavior_tree import Action, Condition, Selector, Sequence, Status
from ai.navigation import find_path
from puzzles.switch_puzzle import impossible_puzzle, solve_puzzle
from ui.inspector import Inspector, active_branch


def make_state(**changes):
    state = {
        "has_key": False, "puzzle_solved": False, "exit_open": False,
        "level_complete": False, "spikes_blocking": False,
        "key_position": (2, 4), "puzzle_position": (5, 6), "exit_position": (7, 8),
    }
    state.update(changes)
    return state


def branch_for(**changes):
    agent = AgentController(make_state(**changes))
    agent.update()
    return active_branch(agent.tree)


def text_of(inspector):
    return "\n".join(text for text, _ in inspector.lines())


def test_branch_is_empty_before_first_tick():
    assert active_branch(AgentController(make_state()).tree) == []


def test_branch_follows_the_controllers_decision():
    assert branch_for() == ["Choose Goal", "Find Key", "Choose Key"]
    assert branch_for(has_key=True) == ["Choose Goal", "Solve Puzzle", "Choose Puzzle"]
    assert branch_for(has_key=True, puzzle_solved=True, exit_open=True) == ["Choose Goal", "Reach Exit", "Choose Exit"]
    assert branch_for(spikes_blocking=True) == ["Choose Goal", "Handle Spikes", "Wait for Spikes"]


def test_branch_when_nothing_is_available_stops_at_root():
    assert branch_for(has_key=True, puzzle_solved=True) == ["Choose Goal"]


def test_branch_ignores_stale_status_from_earlier_ticks():
    state = make_state()
    agent = AgentController(state)
    agent.update()
    state["has_key"] = True
    agent.update()
    assert active_branch(agent.tree)[1] == "Solve Puzzle"


def test_branch_through_nested_sequence_of_successes():
    tree = Sequence([Condition(lambda: True, "Ok"), Action(lambda: Status.SUCCESS, "Do")], "Root")
    tree.tick()
    assert active_branch(tree) == ["Root", "Do"]
    tree = Selector([tree], "Top")
    tree.tick()
    assert active_branch(tree) == ["Top", "Root", "Do"]


def test_panel_shows_real_algorithm_output():
    inspector = Inspector()
    agent = AgentController(make_state())
    inspector.from_decision(agent.update(), agent.tree)
    grid = [[0] * 5 for _ in range(5)]
    inspector.from_path(find_path(grid, (0, 0), (4, 4)))
    inspector.from_puzzle(solve_puzzle())
    text = text_of(inspector)
    assert "Goal: FIND_KEY" in text
    assert "> Choose Key" in text
    assert "Path length: 8" in text
    assert "route found" in text
    assert "Solved" in text


def test_panel_reports_failures():
    inspector = Inspector()
    inspector.from_path(find_path([[0, 1, 0]], (0, 0), (0, 2)))
    inspector.from_puzzle(solve_puzzle(impossible_puzzle()))
    text = text_of(inspector)
    assert "NO ROUTE" in text
    assert "No solution" in text


def test_events_keep_only_the_most_recent_newest_first():
    inspector = Inspector(max_events=3)
    for step in range(5):
        inspector.record(step, "BT", f"event {step}")
    assert [e["step"] for e in inspector.events] == [2, 3, 4]
    text = text_of(inspector)
    assert "event 0" not in text
    assert text.index("event 4") < text.index("event 2")


def test_reset_clears_everything():
    inspector = Inspector()
    inspector.record(0, "BT", "hello")
    inspector.update(goal="FIND_KEY")
    inspector.reset()
    assert not inspector.events
    assert "Goal: -" in text_of(inspector)


def test_draw_fills_only_the_panel():
    pygame.init()
    surface = pygame.Surface((400, 300))
    surface.fill((255, 0, 0))
    inspector = Inspector()
    inspector.record(1, "A*", "path found")
    inspector.draw(surface, pygame.Rect(100, 0, Inspector.WIDTH, 300))
    assert surface.get_at((50, 50)) == (255, 0, 0)
    assert surface.get_at((395, 295)) != (255, 0, 0)
