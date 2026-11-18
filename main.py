"""RogueMind autonomous demo with synchronized playback and route replanning.

Existing A*, Behaviour Tree, CSP, rendering, and robot movement algorithms
remain unchanged. Spike time uses simulation dt, and blocked routes replan.
"""
import pygame
from ai.agent_controller import AgentController
from ai.navigation import find_path
from game.state import WorldState
from game.interactions import collect_key, unlock_door, complete_puzzle, complete_level
from game import obstacles, renderer
from game.movement import RobotMovement
from puzzles.switch_puzzle import solve_puzzle
from ui.playback_controls import Playback
from ui.inspector import Inspector

LEVEL_ID = "ember_crypt"
FPS = 60
INSPECTOR_WIDTH = 320
PLAYBACK_HEIGHT = 44
DISPLAY_WIDTH = renderer.WINDOW_WIDTH + INSPECTOR_WIDTH
DISPLAY_HEIGHT = renderer.WINDOW_HEIGHT + PLAYBACK_HEIGHT


def at_goal(robot, target):
    if robot.state.player_position != target:
        return False
    x, y = robot.grid_to_pixel(*target)
    return abs(robot.robot_x - x) < 0.01 and abs(robot.robot_y - y) < 0.01


def centered_on_tile(robot):
    x, y = robot.grid_to_pixel(*robot.state.player_position)
    return abs(robot.robot_x - x) < 0.01 and abs(robot.robot_y - y) < 0.01


def route_blocked_ahead(robot, state):
    """Detect a newly blocked tile anywhere in the remaining A* route."""
    if robot.crossing_spikes or robot.route_index >= len(robot.route):
        return False
    grid = state.get_ai_grid()
    for row, col in robot.route[robot.route_index:]:
        if not (0 <= row < len(grid) and 0 <= col < len(grid[row])):
            return True
        if grid[row][col] != 0:
            return True
    return False


def _create_display():
    info = pygame.display.Info()
    monitor_width = info.current_w if info.current_w > 0 else 1280
    monitor_height = info.current_h if info.current_h > 0 else 800
    width = min(DISPLAY_WIDTH, max(900, monitor_width - 80))
    height = min(DISPLAY_HEIGHT, max(620, monitor_height - 100))
    return pygame.display.set_mode((width, height), pygame.RESIZABLE)


def main():
    pygame.init()
    screen = _create_display()
    pygame.display.set_caption("RogueMind | Autonomous AI Escape Room")
    logical_screen = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT)).convert()
    game_surface = pygame.Surface((renderer.WINDOW_WIDTH, renderer.WINDOW_HEIGHT)).convert()
    inspector = Inspector()
    clock = pygame.time.Clock()
    sprites = renderer.load_sprites()
    state = WorldState(LEVEL_ID)
    robot = RobotMovement(state)
    agent = AgentController(state, robot)
    obstacles.reset_spikes()

    active_goal = None
    active_target = None
    last_search = None
    puzzle_result = None
    puzzle_started_at = None
    message = "AI is exploring the dungeon"
    previous_reported_goal = None

    def reset_game():
        nonlocal active_goal, active_target, last_search, puzzle_result, puzzle_started_at, message, previous_reported_goal
        robot.reset()
        obstacles.reset_spikes()
        active_goal = None
        active_target = None
        last_search = None
        puzzle_result = None
        puzzle_started_at = None
        message = "Simulation restarted"
        previous_reported_goal = None
        inspector.reset()
        inspector.record("RESET", "Playback", "Simulation restarted")

    playback = Playback(on_reset=reset_game, step_dt=1.0/FPS, start_paused=False)
    decision = {"goal":None,"target":None,"reason":"Ready"}
    running = True
    while running:
        real_dt = min(clock.tick(FPS) / 1000.0, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            else:
                # Playback button positions are in logical-screen coordinates.
                if event.type == pygame.MOUSEBUTTONDOWN:
                    sx, sy = screen.get_size()
                    lx, ly = logical_screen.get_size()
                    event = pygame.event.Event(event.type, {
                        **event.dict,
                        "pos": (round(event.pos[0] * lx / sx), round(event.pos[1] * ly / sy))
                    })
                playback.handle_event(event)

        dt = playback.sim_dt(real_dt)
        if dt > 0:
            obstacles.update_spikes(dt)
            # Remove stale statuses so the inspector shows the CURRENT BT branch.
            def clear_bt_status(node):
                node.last_status = None
                for child in getattr(node, "children", ()):
                    clear_bt_status(child)
            clear_bt_status(agent.tree)
            decision = agent.update()
            goal, target = decision["goal"], decision["target"]
            inspector.from_decision(decision, agent.tree)
            if goal != previous_reported_goal:
                inspector.record("GOAL", "BT", f"{goal}: {decision.get('reason') or 'No reason'}")
                previous_reported_goal = goal

            if goal == "LEVEL_COMPLETE":
                message = "ESCAPED! The AI completed the dungeon."
            elif goal == "WAIT_FOR_SPIKES":
                message = "AI waiting for spikes to retract"
                robot.is_moving = False
            elif goal == "NO_AVAILABLE_GOAL":
                message = decision["reason"]
                robot.is_moving = False
            elif goal is not None and target is not None:
                changed_goal = goal != active_goal or target != active_target
                if changed_goal:
                    active_goal, active_target = goal, target

                # If a tile becomes blocked mid-transition, return the sprite
                # to its last valid logical tile before replanning. WorldState
                # still holds that tile until movement completes.
                if route_blocked_ahead(robot, state) and not centered_on_tile(robot):
                    robot.robot_x, robot.robot_y = robot.grid_to_pixel(*state.player_position)
                    robot.is_moving = False
                needs_route = (changed_goal or route_blocked_ahead(robot, state)
                               or (robot.route_index >= len(robot.route)
                                   and not at_goal(robot, target)))
                if needs_route and not robot.crossing_spikes and centered_on_tile(robot):
                    last_search = find_path(state.get_ai_grid(), state.player_position, target)
                    inspector.from_path(last_search, "A*")
                    inspector.record("PATH", "A*", f"{'Route found' if last_search['found'] else 'No route'}; {last_search['nodes_explored']} nodes explored")
                    if last_search["found"] and robot.set_route(last_search["path"]):
                        message = ("A*: replanned around changed obstacle"
                                   if not changed_goal else decision["reason"])
                    else:
                        message = f"No route available for {goal}"
                        robot.is_moving = False
                if not at_goal(robot, target):
                    # Movement itself refuses to enter blocked cells.
                    # Don't advance a stale route while waiting for a replan.
                    if not route_blocked_ahead(robot, state):
                        robot.update(dt)
                    else:
                        robot.is_moving = False
                else:
                    robot.is_moving = False
                    if goal == "FIND_KEY":
                        if collect_key(state):
                            message = "AI collected the key"
                            inspector.record("WORLD", "Key", "Collected")
                    elif goal == "UNLOCK_DOOR":
                        if unlock_door(state):
                            message = "AI unlocked the door"
                            inspector.record("WORLD", "Door", "Unlocked")
                    elif goal == "SOLVE_PUZZLE":
                        if puzzle_result is None:
                            puzzle_result = solve_puzzle()
                            inspector.from_puzzle(puzzle_result)
                            inspector.record("CSP", "Puzzle", f"{'Solved' if puzzle_result.solved else 'Unsolvable'} using {puzzle_result.strategy}")
                            puzzle_started_at = playback.sim_time
                            message = "CSP: configuring five colour switches"
                        if not puzzle_result.solved:
                            message = "CSP puzzle has no solution"
                        elif (puzzle_started_at is not None
                              and playback.sim_time - puzzle_started_at >= 1.5):
                            if complete_puzzle(state, puzzle_result.solved):
                                message = "CSP solved: switch assignments applied"
                                inspector.record("WORLD", "Puzzle", "Completed")
                    elif goal == "REACH_EXIT":
                        if complete_level(state):
                            message = "ESCAPED! The AI completed the dungeon."
                            inspector.record("WORLD", "Exit", "Level completed")

        # Keep rendering during pause, but freeze all simulation changes.
        renderer.draw_level(game_surface, sprites, state.level_id, state,
                            puzzle_result=puzzle_result,
                            puzzle_started_at=(None if puzzle_started_at is None else
                                               pygame.time.get_ticks() - int((playback.sim_time - puzzle_started_at) * 1000)))
        frames = sprites["robot"][("walk" if robot.is_moving else "idle", robot.direction)]
        if dt > 0:
            robot.update_animation(len(frames))
        renderer.draw_robot(game_surface, sprites, robot)
        renderer.draw_hud(game_surface, state, decision, last_search,
                          puzzle_result=puzzle_result)
        logical_screen.fill((22, 22, 32))
        logical_screen.blit(game_surface, (0, 0))
        inspector.update(
            keys=f"{int(state.has_key)}/1",
            position=state.player_position,
            puzzle_world="Complete" if state.puzzle_solved else "Incomplete",
            puzzle=("Completed" if state.puzzle_solved else
                    "Solution found (not yet applied)" if puzzle_result and puzzle_result.solved else
                    "No solution" if puzzle_result else "Not started"),
        )
        inspector.draw(logical_screen, pygame.Rect(renderer.WINDOW_WIDTH, 0,
                                                  INSPECTOR_WIDTH, renderer.WINDOW_HEIGHT))
        playback.draw(logical_screen, pygame.Rect(0, renderer.WINDOW_HEIGHT,
                                                  DISPLAY_WIDTH, PLAYBACK_HEIGHT))
        if screen.get_size() == logical_screen.get_size():
            screen.blit(logical_screen, (0, 0))
        else:
            pygame.transform.scale(logical_screen, screen.get_size(), screen)
        goal = decision.get("goal")
        pygame.display.set_caption(f"RogueMind | AI: {goal or 'THINKING'}")
        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    main()
