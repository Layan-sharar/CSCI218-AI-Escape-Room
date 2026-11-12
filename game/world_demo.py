from game.interactions import (
    collect_key,
    complete_level,
    complete_puzzle,
    unlock_door,
)
from game.movement import move_player
from game.state import WorldState


def main():
    state = WorldState("ember_crypt")
    print("Starting position:", state.player_position)

    # Walk to the key, then to the locked door.
    route = [
        (1, 2),
        (1, 3),
        (1, 4),
        (2, 4),
    ]

    for position in route:
        moved = move_player(state, position)
        print("Move to", position, ":", moved)

        if not moved:
            print("The demo stopped because that move was blocked.")
            return

        if state.player_position == state.key_position:
            print("Key collected:", collect_key(state))

        if state.player_position == (2, 4):
            print("Door unlocked:", unlock_door(state))

    # Go through the door, solve the puzzle, and reach the exit.
    route_after_door = [
        (3, 4),
        (3, 5),
        (3, 6),
        (3, 7),
        (4, 7),
        (5, 7),
    ]

    for position in route_after_door:
        moved = move_player(state, position)
        print("Move to", position, ":", moved)

        if not moved:
            print("The demo stopped because that move was blocked.")
            return

        if state.player_position == state.puzzle_position:
            print("Puzzle solved:", complete_puzzle(state, True))

    print("Level complete:", complete_level(state))

    # Show that reset returns the player and progress to the start.
    state.reset()
    print("After reset:")
    print("Position:", state.player_position)
    print("Has key:", state.has_key)
    print("Door unlocked:", state.door_unlocked)
    print("Puzzle solved:", state.puzzle_solved)
    print("Level complete:", state.level_complete)


if __name__ == "__main__":
    main()