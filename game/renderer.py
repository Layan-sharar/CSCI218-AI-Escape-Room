
import pygame

# Screen dimensions
screen_width = 800
screen_height = 800

# Load dungeon tileset
dungeon_tileset = pygame.image.load("assets/tilesets/Dungeon_Tileset.png").convert_alpha()

# Extract dungeon room
dungeon_room_tile = dungeon_tileset.subsurface((8, 0, 80, 72))

# Scale dungeon to screen size
scaled_dungeon_tileset = pygame.transform.scale(
    dungeon_room_tile, (screen_width, screen_height)
)

# Function to load robot animation frames
def load_animation(action, direction, frame_count):
    frames = []

    for i in range(frame_count):
        frame = pygame.image.load(
            f"assets/sprites/robot/frames/helper_robot_{action}_{direction}_{i:02d}.png"
        ).convert_alpha()

        scaled_frame = pygame.transform.scale(frame, (80,80))
        frames.append(scaled_frame)

    return frames

spike_frames={}
for i in range (1,5):
    frame=pygame.image.load(f"assets/sprites/traps/peaks_{i}.png").convert_alpha()
    frame=pygame.transform.scale(frame, (64,64))
    spike_frames[i] = frame
# Load idle animation
idle_frames = load_animation("idle", "south", 4)

# Load walking animations
walk_frames = {
    "north": load_animation("walk", "north", 6),
    "south": load_animation("walk", "south", 6),
    "east": load_animation("walk", "east", 6),
    "west": load_animation("walk", "west", 6)
}
