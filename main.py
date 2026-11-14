
import pygame
import game.levels as levels
import game.obstacles as obstacles
from ai.agent_controller import AgentController

pygame.init()

game_state = {
    "has_key": False,
    "puzzle_solved": False,
    "exit_open": False,
    "level_complete": False,
    "spikes_blocking": False,
    "key_position": (2, 4),
    "puzzle_position": (5, 6),
    "exit_position": (7, 8)
}

agent = AgentController(game_state)


# Create the window before importing renderer
screen = pygame.display.set_mode(
    (levels.screen_width, levels.screen_height)
)
pygame.display.set_caption("AI Escape Room!")

import game.renderer as renderer
import game.movement as movement

clock = pygame.time.Clock()
running = True

while running:
    # Time elapsed since previous frame (seconds)
    dt = clock.tick(60) / 1000.0

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                movement.reset_movement()

    # Update obstacle animations
    obstacles.update_spikes()

    # Check whether the next crossing is unsafe
    game_state["spikes_blocking"] = (
        movement.is_next_crossing_blocked()
    )

    # Ask the Behavior Tree what to do
    decision = agent.update()
    pygame.display.set_caption(
    f"RogueMind | AI Decision: {decision['goal']}"
)
    if decision["goal"] not in (
    "WAIT_FOR_SPIKES",
    "LEVEL_COMPLETE",
    "NO_AVAILABLE_GOAL"
    ):
        movement.move_towards_target(dt)

    else:
        movement.is_moving = False

    # Select animation based on movement
    if movement.is_moving:
        current_frames = renderer.walk_frames[movement.direction]
    else:
        current_frames = renderer.idle_frames

    # Update animation frame
    movement.update_animation(len(current_frames))

    # Get robot's pixel position
    x = round(movement.robot_x)
    y = round(movement.robot_y)

    # Draw dungeon
    screen.blit(renderer.scaled_dungeon_tileset, (0, 0))
    
    # Select the current spike sprite
    spike_frame = obstacles.get_spike_frame()
    spike_sprite = renderer.spike_frames[spike_frame]

    # Position the spike in its grid cell
    spike_x = obstacles.spike_col * levels.cell_width
    spike_y = obstacles.spike_row * levels.cell_height

    screen.blit(
        spike_sprite,
        (round(spike_x), round(spike_y))
    )

    # Draw robot
    screen.blit(
        current_frames[movement.frame_index % len(current_frames)],
        (x, y)
    )

    # Update display
    pygame.display.flip()

pygame.quit()
