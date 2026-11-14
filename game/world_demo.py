from collections import deque

from game.interactions import (
    collect_key,
    complete_level,
    complete_puzzle,
    unlock_door,
)
from game.movement import move_player
from game.state import WorldState


def find_route(state, targets):
    """Find a shortest walkable route through the maze to any target cell."""
    targets = {tuple(position) for position in targets}
    grid = state.get_ai_grid()
    start = state.player_position
    frontier = deque([start])
    previous = {start: None}

    while frontier:
        position = frontier.popleft()
        if position in targets:
            route = []
            while position != start:
                route.append(position)
                position = previous[position]
            route.reverse()
            return route

        row, column = position
        for neighbor in (
            (row - 1, column),
            (row + 1, column),
            (row, column - 1),
            (row, column + 1),
        ):
            next_row, next_column = neighbor
            if (
                0 <= next_row < len(grid)
                and 0 <= next_column < len(grid[next_row])
                and grid[next_row][next_column] == 0
                and neighbor not in previous
            ):
                previous[neighbor] = position
                frontier.append(neighbor)

    return None


def walk_route(state, route, destination):
    """Follow a route one tile at a time, triggering items and puzzles."""
    if route is None:
        print("No walkable route to", destination, "was found.")
        return False

    for position in route:
        if not move_player(state, position):
            print("The route became blocked at", position)
            return False

        if state.player_position == state.key_position and not state.has_key:
            print("Key collected:", collect_key(state))

        if state.player_position == state.puzzle_position and not state.puzzle_solved:
            print("Puzzle solved:", complete_puzzle(state, True))

    print("Reached", destination, "after", len(route), "maze steps.")
    return True


def main():
    state = WorldState("ember_crypt")
    print("Starting position:", state.player_position)

    if not walk_route(state, find_route(state, [state.key_position]), "the key"):
        return

    door_row, door_column = state.door_position
    door_neighbors = [
        (door_row - 1, door_column),
        (door_row + 1, door_column),
        (door_row, door_column - 1),
        (door_row, door_column + 1),
    ]
    if not walk_route(state, find_route(state, door_neighbors), "the locked door"):
        return

    print("Door unlocked:", unlock_door(state))

    if not walk_route(state, find_route(state, [state.puzzle_position]), "the puzzle"):
        return

    if not walk_route(state, find_route(state, [state.exit_position]), "the exit"):
        return

    print("Level complete:", complete_level(state))

    state.reset()
    print("After reset:")
    print("Position:", state.player_position)
    print("Has key:", state.has_key)
    print("Door unlocked:", state.door_unlocked)
    print("Puzzle solved:", state.puzzle_solved)
    print("Level complete:", state.level_complete)


if __name__ == "__main__":
    main()
