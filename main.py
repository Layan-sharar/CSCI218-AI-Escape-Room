"""RogueMind autonomous demo with a fixed full-map view.

The AI / A* / behavior-tree / CSP logic is unchanged. This file only drives
existing modules and presents the entire escape room at once.
"""
import pygame

from ai.agent_controller import AgentController
from ai.navigation import find_path
from game.state import WorldState
from game.interactions import collect_key, unlock_door, complete_puzzle, complete_level
from game import obstacles, renderer
from game.movement import RobotMovement
from puzzles.switch_puzzle import solve_puzzle, default_puzzle
from ui.inspector import Inspector
from ui.playback_controls import Playback
from ui.puzzle_view import PuzzleView, SIZE as PUZZLE_SIZE

LEVEL_ID = "ember_crypt"
FPS = 60
CONTROL_HEIGHT = 60


def at_goal(robot, target):
    if robot.state.player_position != target:
        return False
    x, y = robot.grid_to_pixel(*target)
    return abs(robot.robot_x - x) < 0.01 and abs(robot.robot_y - y) < 0.01


def _create_display():
    info = pygame.display.Info()
    monitor_width = info.current_w if info.current_w > 0 else 1280
    monitor_height = info.current_h if info.current_h > 0 else 800
    width = min(renderer.WINDOW_WIDTH + Inspector.WIDTH, max(900, monitor_width - 80))
    height = min(renderer.WINDOW_HEIGHT + CONTROL_HEIGHT, max(620, monitor_height - 100))
    return pygame.display.set_mode((width, height), pygame.RESIZABLE)


def main():
    pygame.init()
    screen = _create_display()
    pygame.display.set_caption("RogueMind | Autonomous AI Escape Room")
    game_surface = pygame.Surface((renderer.WINDOW_WIDTH, renderer.WINDOW_HEIGHT)).convert()
    logical_screen = pygame.Surface((renderer.WINDOW_WIDTH + Inspector.WIDTH,
                                     renderer.WINDOW_HEIGHT + CONTROL_HEIGHT)).convert()
    inspector_rect = pygame.Rect(renderer.WINDOW_WIDTH, 0, Inspector.WIDTH, renderer.WINDOW_HEIGHT)
    controls_rect = pygame.Rect(0, renderer.WINDOW_HEIGHT, logical_screen.get_width(), CONTROL_HEIGHT)
    inspector = Inspector()
    show_puzzle = False
    puzzle_view = None
    puzzle_surface = pygame.Surface(PUZZLE_SIZE)
    clock = pygame.time.Clock()
    sprites = renderer.load_sprites()

    state = WorldState(LEVEL_ID)
    robot = RobotMovement(state)
    agent = AgentController(state, robot)
    active_goal = None
    active_target = None
    last_search = None
    puzzle_result = None
    puzzle_started_at = None
    message = "AI is exploring the dungeon"
    step_number = 0
    last_logged_goal = None

    def reset_world():
        nonlocal active_goal, active_target, last_search, puzzle_result
        nonlocal puzzle_started_at, message, puzzle_view, step_number, last_logged_goal
        robot.reset()
        active_goal = active_target = last_search = puzzle_result = None
        puzzle_started_at = None
        puzzle_view = None
        step_number = 0
        last_logged_goal = None
        inspector.reset()
        clear_tree_status(agent.tree)
        message = "Simulation restarted"
        # Reset trap phase without changing the existing obstacle algorithm.
        obstacles.frame_index = 0
        obstacles.last_spike_time = pygame.time.get_ticks()

    def clear_tree_status(node):
        # The Inspector must show only nodes visited on this decision tick.
        node.last_status = None
        for child in getattr(node, 'children', []):
            clear_tree_status(child)

    playback = Playback(on_reset=reset_world, start_paused=False)
    running = True

    while running:
        real_dt = min(clock.tick(FPS) / 1000.0, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_i:
                show_puzzle = not show_puzzle
            else:
                # Mouse coordinates are mapped from the resized window back to
                # the logical panel so the buttons remain clickable.
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x = round(event.pos[0] * logical_screen.get_width() / screen.get_width())
                    y = round(event.pos[1] * logical_screen.get_height() / screen.get_height())
                    event = pygame.event.Event(event.type, {**event.dict, 'pos': (x, y)})
                playback.handle_event(event)

        dt = playback.sim_dt(real_dt)
        # Existing spikes use pygame.get_ticks(), not dt. Shift their time
        # origin to keep them in step with pause and speed controls.
        obstacles.last_spike_time += round((real_dt - dt) * 1000)
        if puzzle_started_at is not None:
            puzzle_started_at += round((real_dt - dt) * 1000)

        if dt > 0:
            obstacles.update_spikes()
            clear_tree_status(agent.tree)
            decision = agent.update()
            step_number += 1
        else:
            decision = {'goal': agent.current_goal, 'target': agent.target_position,
                        'reason': agent.reason}
            robot.is_moving = False

        if dt > 0:
            inspector.from_decision(decision, agent.tree)
            if decision['goal'] != last_logged_goal:
                inspector.record(step_number, 'BT', f"Goal: {decision['goal']}")
                last_logged_goal = decision['goal']
        goal, target = decision["goal"], decision["target"]

        if dt > 0:
            if goal == "LEVEL_COMPLETE":
                message = "ESCAPED! The AI completed the dungeon."
            elif goal == "WAIT_FOR_SPIKES":
                message = "AI waiting for spikes to retract"
                robot.is_moving = False
            elif goal == "NO_AVAILABLE_GOAL":
                message = decision["reason"]
                robot.is_moving = False
            elif goal is not None and target is not None:
                if goal != active_goal or target != active_target:
                    active_goal, active_target = goal, target
                    if not robot.crossing_spikes:
                        last_search = find_path(state.get_ai_grid(), state.player_position, target)
                        inspector.from_path(last_search)
                        inspector.record(step_number, 'A*', f"{goal}: {'route found' if last_search['found'] else 'no route'}")
                        if last_search["found"] and robot.set_route(last_search["path"]):
                            message = decision["reason"]
                        else:
                            message = f"No route available for {goal}"
                elif robot.route_index >= len(robot.route) and not at_goal(robot, target):
                    last_search = find_path(state.get_ai_grid(), state.player_position, target)
                    inspector.from_path(last_search)
                    inspector.record(step_number, 'A*', f"Replan: {'route found' if last_search['found'] else 'no route'}")
                    if last_search["found"]:
                        robot.set_route(last_search["path"])

                if not at_goal(robot, target):
                    robot.update(dt)
                else:
                    robot.is_moving = False
                    if goal == "FIND_KEY":
                        if collect_key(state):
                            message = "AI collected the key"
                            inspector.record(step_number, 'World', 'Key collected')
                    elif goal == "UNLOCK_DOOR":
                        if unlock_door(state):
                            message = "AI unlocked the door"
                            inspector.record(step_number, 'World', 'Door unlocked')
                    elif goal == "SOLVE_PUZZLE":
                        # The original CSP solver still determines the solution.
                        # A short visible switch-activation sequence makes the
                        # AI's work observable instead of looking like coin pickup.
                        if puzzle_result is None:
                            puzzle_result = solve_puzzle()
                            inspector.from_puzzle(puzzle_result)
                            puzzle_view = PuzzleView(default_puzzle(), puzzle_result)
                            inspector.record(step_number, 'CSP', 'Solution found' if puzzle_result.solved else 'No solution')
                            puzzle_started_at = pygame.time.get_ticks()
                            message = "CSP: configuring five colour switches"
                        if not puzzle_result.solved:
                            message = "CSP puzzle has no solution"
                        elif (puzzle_started_at is not None and
                              pygame.time.get_ticks() - puzzle_started_at >= 1500):
                            if complete_puzzle(state, puzzle_result.solved):
                                message = "CSP solved: switch assignments applied"
                                inspector.record(step_number, 'World', 'Puzzle completed')
                    elif goal == "REACH_EXIT":
                        if complete_level(state):
                            message = "ESCAPED! The AI completed the dungeon."
                            inspector.record(step_number, 'World', 'Level completed')

        logical_screen.fill((22, 22, 32))
        renderer.draw_level(game_surface, sprites, state.level_id, state,
                            puzzle_result=puzzle_result,
                            puzzle_started_at=puzzle_started_at)
        frames = sprites["robot"][("walk" if robot.is_moving else "idle", robot.direction)]
        robot.update_animation(len(frames))
        renderer.draw_robot(game_surface, sprites, robot)
        renderer.draw_hud(game_surface, state, decision, last_search,
                          puzzle_result=puzzle_result)

        logical_screen.blit(game_surface, (0, 0))
        playback.draw(logical_screen, controls_rect)
        if puzzle_view is not None and puzzle_started_at is not None:
            count = min(len(puzzle_view.puzzle.switches),
                        max(0, (pygame.time.get_ticks() - puzzle_started_at) // 300))
            while puzzle_view.steps_applied < count:
                puzzle_view.apply_next()
        inspector.update(keys=f"{int(state.has_key)}/1", position=state.player_position, step=step_number,
                         puzzle_world='Complete' if state.puzzle_solved else 'Incomplete',
                         puzzle_progress=(f'{puzzle_view.steps_applied}/{len(puzzle_view.puzzle.switches)}'
                                          if puzzle_view is not None else '0/5'))
        # Refresh the panel after collecting the latest state and switch progress.
        inspector.draw(logical_screen, inspector_rect)
        if show_puzzle and puzzle_view is not None:
            # Optional CSP detail overlay; existing in-dungeon switches stay visible.
            puzzle_view.draw(puzzle_surface)
            x = max(0, (renderer.WINDOW_WIDTH - PUZZLE_SIZE[0]) // 2)
            y = max(0, (renderer.WINDOW_HEIGHT - PUZZLE_SIZE[1]) // 2)
            logical_screen.blit(puzzle_surface, (x, y))

        if screen.get_size() == logical_screen.get_size():
            screen.blit(logical_screen, (0, 0))
        else:
            pygame.transform.scale(logical_screen, screen.get_size(), screen)

        pygame.display.set_caption(f"RogueMind | AI: {goal or 'THINKING'}")
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
