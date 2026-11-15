"""Play / Pause / Step / Reset / Speed controls for the simulation.

The controls only decide how much simulation time passes each frame; the
agent's decisions are untouched. The game loop asks for that time:

    playback = Playback(on_reset=reset_world)
    for event in pygame.event.get():
        playback.handle_event(event)
    dt = playback.sim_dt(clock.tick(60) / 1000)   # 0 while paused
    playback.draw(screen, pygame.Rect(0, 800, 800, 60))

Keys: SPACE play/pause, N single step, R reset, +/- speed. Buttons can be clicked too.
"""

import pygame

SPEEDS = (0.5, 1, 2, 4)
BG, BUTTON, ACTIVE, FG = (22, 22, 32), (55, 55, 75), (90, 70, 160), (235, 235, 240)


class Playback:
    def __init__(self, on_reset=None, step_dt=0.5, start_paused=True):
        # step_dt: simulation seconds one Single Step advances (0.5 s = one tile at the robot's speed)
        self.on_reset = on_reset
        self.step_dt = step_dt
        self.start_paused = start_paused
        self.speed_index = SPEEDS.index(1)
        self.buttons = {}
        self._font = None
        self.reset(notify=False)

    @property
    def speed(self):
        return SPEEDS[self.speed_index]

    def play(self):
        self.paused = False

    def pause(self):
        self.paused = True

    def toggle(self):
        self.paused = not self.paused

    def step(self):
        """Pause, then let exactly one step_dt of simulation time pass on the next frame."""
        self.paused = True
        self._step_pending = True

    def change_speed(self, delta):
        self.speed_index = max(0, min(len(SPEEDS) - 1, self.speed_index + delta))

    def reset(self, notify=True):
        self.paused = self.start_paused
        self._step_pending = False
        self.ticks = 0
        self.sim_time = 0.0
        if notify and self.on_reset:
            self.on_reset()

    def sim_dt(self, real_dt):
        """Simulation seconds to advance this frame."""
        if self._step_pending:
            self._step_pending = False
            dt = self.step_dt
        elif self.paused:
            return 0.0
        else:
            dt = real_dt * self.speed
        self.ticks += 1
        self.sim_time += dt
        return dt

    def handle_event(self, event):
        """Apply a key press or button click. Returns True if the event was used."""
        actions = {
            "play": self.toggle,
            "step": self.step,
            "reset": self.reset,
            "slower": lambda: self.change_speed(-1),
            "faster": lambda: self.change_speed(1),
        }
        keys = {
            pygame.K_SPACE: "play", pygame.K_n: "step", pygame.K_r: "reset",
            pygame.K_MINUS: "slower", pygame.K_KP_MINUS: "slower",
            pygame.K_EQUALS: "faster", pygame.K_PLUS: "faster", pygame.K_KP_PLUS: "faster",
        }
        name = None
        if event.type == pygame.KEYDOWN:
            name = keys.get(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            name = next((n for n, r in self.buttons.items() if r.collidepoint(event.pos)), None)
        if name:
            actions[name]()
        return name is not None

    def draw(self, surface, rect):
        if self._font is None:
            pygame.font.init()
            self._font = pygame.font.Font(None, 22)
        surface.fill(BG, rect)
        labels = [
            ("play", "Play" if self.paused else "Pause", not self.paused),
            ("step", "Step", False),
            ("reset", "Reset", False),
            ("slower", "-", False),
            ("faster", "+", False),
        ]
        x = rect.left + 10
        h = rect.height - 20
        for name, label, active in labels:
            w = 70 if len(label) > 1 else 30
            r = pygame.Rect(x, rect.top + 10, w, h)
            self.buttons[name] = r
            pygame.draw.rect(surface, ACTIVE if active else BUTTON, r, border_radius=4)
            text = self._font.render(label, True, FG)
            surface.blit(text, text.get_rect(center=r.center))
            x += w + 8
        status = f"{self.speed}x  tick {self.ticks}  t={self.sim_time:.1f}s"
        surface.blit(self._font.render(status, True, FG), (x + 8, rect.centery - 7))


def run_demo():
    """Tiny simulation counter to try the buttons on their own."""
    pygame.init()
    screen = pygame.display.set_mode((560, 140))
    pygame.display.set_caption("Playback controls demo")
    counter = {"value": 0.0}
    playback = Playback(on_reset=lambda: counter.update(value=0.0))
    font = pygame.font.Font(None, 40)
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            else:
                playback.handle_event(event)
        counter["value"] += playback.sim_dt(clock.tick(60) / 1000)
        screen.fill((0, 0, 0))
        screen.blit(font.render(f"Simulated seconds: {counter['value']:.2f}", True, FG), (20, 20))
        playback.draw(screen, pygame.Rect(0, 80, 560, 60))
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    run_demo()
