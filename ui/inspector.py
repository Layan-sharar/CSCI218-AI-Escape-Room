"""AI Inspector: a Pygame side panel that shows what the AI is thinking.

How the game uses it:
    inspector = Inspector()
    inspector.from_decision(agent.update(), agent.tree)   # goal, reason, active BT branch
    inspector.from_path(find_path(grid, start, goal))      # A* stats
    inspector.from_puzzle(solve_puzzle())                  # CSP result
    inspector.record(step, "A*", "Route to key found")     # recent actions list
    inspector.draw(surface, pygame.Rect(800, 0, Inspector.WIDTH, 800))

An event is a plain dict: {"step", "source", "message"}. Any module can call
record(); the panel keeps the most recent few.

To try it alone: python -m ui.inspector
(SPACE play/pause, N step, R reset, +/- speed, ESC quit).
"""

from collections import deque

import pygame

from ai.behavior_tree import Selector, Sequence, Status

BG, FG, DIM = (22, 22, 32), (235, 235, 240), (140, 140, 160)
HEADING, GOOD, BAD = (170, 130, 255), (90, 200, 110), (220, 90, 90)


def active_branch(node):
    """Names of the nodes the last tick went through, root first.

    Reads each node's last_status, so call it right after the tree has ticked.
    Selector: the first child that did not fail. Sequence: the first child that
    did not succeed, or its last child if all of them succeeded.
    """
    if node.last_status is None:
        return []
    names = [node.name]
    children = getattr(node, "children", [])
    if isinstance(node, Selector):
        child = next((c for c in children if c.last_status != Status.FAILURE), None)
    elif isinstance(node, Sequence):
        child = next((c for c in children if c.last_status != Status.SUCCESS), children[-1] if children else None)
    else:
        child = None
    return names + active_branch(child) if child else names


class Inspector:
    WIDTH = 320

    def __init__(self, max_events=8):
        self.events = deque(maxlen=max_events)
        self.reset()

    def reset(self):
        self.events.clear()
        self.metrics = {}
        self._fonts = None

    def record(self, step, source, message):
        event = {"step": step, "source": source, "message": message}
        self.events.append(event)
        return event

    def update(self, **metrics):
        """Set any displayed value directly, e.g. update(keys="1/1", position=(3, 4))."""
        self.metrics.update(metrics)

    def from_decision(self, decision, tree=None):
        self.update(
            goal=decision.get("goal"),
            reason=decision.get("reason", ""),
            target=decision.get("target"),
            branch=active_branch(tree) if tree else [],
        )

    def from_path(self, result, algorithm="A*"):
        self.update(
            algorithm=algorithm,
            path_found=result["found"],
            path_length=result["path_length"],
            nodes_explored=result["nodes_explored"],
            search_ms=result["runtime"] * 1000,
        )

    def from_puzzle(self, result):
        self.update(
            puzzle="Solved" if result.solved else "No solution",
            puzzle_strategy=result.strategy,
            puzzle_assignments=result.stats.assignments,
            puzzle_backtracks=result.stats.backtracks,
        )

    def lines(self):
        """The panel's text as (text, colour) pairs, so it can be tested without drawing."""
        m = self.metrics
        out = [("AI Inspector", HEADING), ("", FG)]
        out.append((f"Goal: {m.get('goal') or '-'}", FG))
        if m.get("reason"):
            out.append((f"  {m['reason']}", DIM))
        out.append(("Behaviour Tree:", HEADING))
        for depth, name in enumerate(m.get("branch") or ["-"]):
            out.append((f"{'  ' * depth}> {name}", FG))
        out.append(("Pathfinding:", HEADING))
        if "path_found" in m:
            out.append((f"  {m['algorithm']}: {'route found' if m['path_found'] else 'NO ROUTE'}",
                        GOOD if m["path_found"] else BAD))
            out.append((f"  Path length: {m['path_length']}", FG))
            out.append((f"  Nodes explored: {m['nodes_explored']}", FG))
            out.append((f"  Search time: {m['search_ms']:.2f} ms", FG))
        else:
            out.append(("  -", DIM))
        out.append(("Puzzle:", HEADING))
        out.append((f"  {m.get('puzzle', 'Not started')}", FG))
        if "puzzle_strategy" in m:
            out.append((f"  CSP: {m['puzzle_strategy']}", DIM))
            out.append((f"  {m['puzzle_assignments']} assignments, {m['puzzle_backtracks']} backtracks", DIM))
        extras = [(k, m[k]) for k in ("keys", "position", "step") if k in m]
        if extras:
            out.append(("Agent:", HEADING))
            out += [(f"  {k.capitalize()}: {v}", FG) for k, v in extras]
        out.append(("Recent actions:", HEADING))
        for e in reversed(self.events):
            out.append((f"  [{e['step']}] {e['source']}: {e['message']}", FG))
        return out

    def draw(self, surface, rect):
        if self._fonts is None:
            pygame.font.init()
            self._fonts = pygame.font.Font(None, 20)
        surface.fill(BG, rect)
        y = rect.top + 10
        for text, colour in self.lines():
            if y > rect.bottom - 18:
                break
            surface.blit(self._fonts.render(text, True, colour), (rect.left + 10, y))
            y += 18


def run_demo():
    """Tiny sample run: the real Behaviour Tree, A* and CSP on the test grid, drawn with shapes."""
    import game.levels as levels
    from ai.agent_controller import AgentController
    from ai.navigation import find_path
    from puzzles.switch_puzzle import solve_puzzle
    from ui.playback_controls import Playback

    tile = 48
    grid = levels.test_grid
    map_w, map_h = len(grid[0]) * tile, len(grid) * tile
    panel = pygame.Rect(map_w, 0, Inspector.WIDTH, max(map_h, 600))
    controls = pygame.Rect(0, map_h, map_w, 60)

    pygame.init()
    screen = pygame.display.set_mode((panel.right, max(panel.bottom, controls.bottom)))
    pygame.display.set_caption("AI Inspector demo")
    inspector = Inspector()
    sim = {}

    def reset():
        sim["state"] = {
            "has_key": False, "puzzle_solved": False, "exit_open": False,
            "level_complete": False, "spikes_blocking": False,
            "key_position": (2, 4), "puzzle_position": (5, 6), "exit_position": (7, 8),
        }
        sim.update(agent=AgentController(sim["state"]), pos=(3, 1), moves=0, goal=None)
        inspector.reset()

    def tick():
        """One simulation step: decide, plan, move one tile, apply what was reached."""
        state, agent = sim["state"], sim["agent"]
        decision = agent.update()
        inspector.from_decision(decision, agent.tree)
        if decision["goal"] != sim["goal"]:
            sim["goal"] = decision["goal"]
            inspector.record(sim["moves"], "BT", f"New goal {decision['goal']}")
        if decision["target"]:
            result = find_path(grid, sim["pos"], decision["target"])
            inspector.from_path(result)
            if result["found"] and len(result["path"]) > 1:
                sim["pos"] = result["path"][1]
                sim["moves"] += 1
        pos = sim["pos"]
        if pos == state["key_position"] and not state["has_key"]:
            state["has_key"] = True
            inspector.record(sim["moves"], "World", "Picked up key")
        elif pos == state["puzzle_position"] and state["has_key"] and not state["puzzle_solved"]:
            result = solve_puzzle()
            inspector.from_puzzle(result)
            state["puzzle_solved"] = state["exit_open"] = result.solved
            inspector.record(sim["moves"], "CSP", "Switches set, exit open")
        elif pos == state["exit_position"] and state["exit_open"] and not state["level_complete"]:
            state["level_complete"] = True
            inspector.record(sim["moves"], "World", "Reached the exit")
        inspector.update(keys=f"{int(state['has_key'])}/1", position=pos, step=sim["moves"])

    reset()
    playback = Playback(on_reset=reset)
    clock = pygame.time.Clock()
    elapsed = 0.0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            else:
                playback.handle_event(event)

        elapsed += playback.sim_dt(clock.tick(60) / 1000)
        while elapsed >= playback.step_dt:  # one tile per step_dt of simulation time
            elapsed -= playback.step_dt
            tick()

        screen.fill((0, 0, 0))
        for r, row in enumerate(grid):
            for c, cell in enumerate(row):
                pygame.draw.rect(screen, (60, 60, 70) if cell else (110, 100, 90), (c * tile, r * tile, tile - 1, tile - 1))
        state = sim["state"]
        for pos, colour, show in ((state["key_position"], (240, 200, 60), not state["has_key"]),
                                  (state["puzzle_position"], (170, 90, 230), not state["puzzle_solved"]),
                                  (state["exit_position"], GOOD if state["exit_open"] else BAD, True)):
            if show:
                pygame.draw.rect(screen, colour, (pos[1] * tile + 10, pos[0] * tile + 10, tile - 20, tile - 20))
        r, c = sim["pos"]
        pygame.draw.circle(screen, (80, 160, 255), (c * tile + tile // 2, r * tile + tile // 2), tile // 3)
        inspector.draw(screen, panel)
        playback.draw(screen, controls)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    run_demo()
