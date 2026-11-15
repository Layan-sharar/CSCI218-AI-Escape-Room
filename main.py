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
from puzzles.switch_puzzle import solve_puzzle

LEVEL_ID = "ember_crypt"
FPS = 60


def at_goal(robot, target):
    if robot.state.player_position != target:
        return False
    x, y = robot.grid_to_pixel(*target)
    return abs(robot.robot_x - x) < 0.01 and abs(robot.robot_y - y) < 0.01


def _create_display():
    info = pygame.display.Info()
    monitor_width = info.current_w if info.current_w > 0 else 1280
    monitor_height = info.current_h if info.current_h > 0 else 800
    width = min(renderer.WINDOW_WIDTH, max(900, monitor_width - 80))
    height = min(renderer.WINDOW_HEIGHT, max(620, monitor_height - 100))
    return pygame.display.set_mode((width, height), pygame.RESIZABLE)


def main():
    pygame.init()
    screen = _create_display()
    pygame.display.set_caption("RogueMind | Autonomous AI Escape Room")
    logical_screen = pygame.Surface((renderer.WINDOW_WIDTH, renderer.WINDOW_HEIGHT)).convert()
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
    running = True

    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                robot.reset()
                active_goal = active_target = last_search = puzzle_result = None
                puzzle_started_at = None
                message = "Simulation restarted"

        obstacles.update_spikes()
        decision = agent.update()
        goal, target = decision["goal"], decision["target"]

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
                    if last_search["found"] and robot.set_route(last_search["path"]):
                        message = decision["reason"]
                    else:
                        message = f"No route available for {goal}"
            elif robot.route_index >= len(robot.route) and not at_goal(robot, target):
                last_search = find_path(state.get_ai_grid(), state.player_position, target)
                if last_search["found"]:
                    robot.set_route(last_search["path"])

            if not at_goal(robot, target):
                robot.update(dt)
            else:
                robot.is_moving = False
                if goal == "FIND_KEY":
                    if collect_key(state):
                        message = "AI collected the key"
                elif goal == "UNLOCK_DOOR":
                    if unlock_door(state):
                        message = "AI unlocked the door"
                elif goal == "SOLVE_PUZZLE":
                    # The original CSP solver still determines the solution.
                    # A short visible switch-activation sequence makes the
                    # AI's work observable instead of looking like coin pickup.
                    if puzzle_result is None:
                        puzzle_result = solve_puzzle()
                        puzzle_started_at = pygame.time.get_ticks()
                        message = "CSP: configuring five colour switches"
                    if not puzzle_result.solved:
                        message = "CSP puzzle has no solution"
                    elif (puzzle_started_at is not None and
                          pygame.time.get_ticks() - puzzle_started_at >= 1500):
                        if complete_puzzle(state, puzzle_result.solved):
                            message = "CSP solved: switch assignments applied"
                elif goal == "REACH_EXIT":
                    if complete_level(state):
                        message = "ESCAPED! The AI completed the dungeon."

        renderer.draw_level(logical_screen, sprites, state.level_id, state,
                            puzzle_result=puzzle_result,
                            puzzle_started_at=puzzle_started_at)
        frames = sprites["robot"][("walk" if robot.is_moving else "idle", robot.direction)]
        robot.update_animation(len(frames))
        renderer.draw_robot(logical_screen, sprites, robot)
        renderer.draw_hud(logical_screen, state, decision, last_search,
                          puzzle_result=puzzle_result)

        if screen.get_size() == logical_screen.get_size():
            screen.blit(logical_screen, (0, 0))
        else:
            pygame.transform.scale(logical_screen, screen.get_size(), screen)

        pygame.display.set_caption(f"RogueMind | AI: {goal or 'THINKING'}")
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
