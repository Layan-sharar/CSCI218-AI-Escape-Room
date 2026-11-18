"""AI Inspector panel for live RogueMind data (BT, A*, CSP and events)."""
from collections import deque
import pygame
from ai.behavior_tree import Selector, Sequence, Status

BG, FG, DIM = (22,22,32), (235,235,240), (140,140,160)
HEADING, GOOD, BAD = (170,130,255), (90,200,110), (220,90,90)

def active_branch(node):
    """Trace the most recent tree tick; stale statuses are cleared by the caller."""
    if node is None or node.last_status is None:
        return []
    names = [node.name]
    children = getattr(node, 'children', [])
    if isinstance(node, Selector):
        child = next((c for c in children if c.last_status not in (None, Status.FAILURE)), None)
    elif isinstance(node, Sequence):
        child = next((c for c in children if c.last_status not in (None, Status.SUCCESS)), children[-1] if children else None)
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
        event = {'step':step,'source':source,'message':message}
        self.events.append(event)
        return event
    def update(self, **metrics):
        self.metrics.update(metrics)
    def from_decision(self, decision, tree=None):
        self.update(goal=decision.get('goal'), reason=decision.get('reason',''),
                    target=decision.get('target'), branch=active_branch(tree) if tree else [])
    def from_path(self, result, algorithm='A*'):
        self.update(algorithm=algorithm, path_found=result['found'],
                    path_length=result['path_length'], nodes_explored=result['nodes_explored'],
                    search_ms=result['runtime']*1000)
    def from_puzzle(self, result):
        self.update(puzzle='Solution found (not yet applied)' if result.solved else 'No solution',
                    puzzle_strategy=result.strategy,
                    puzzle_assignments=result.stats.assignments,
                    puzzle_backtracks=result.stats.backtracks)
    def lines(self):
        m = self.metrics
        out = [('AI Inspector', HEADING), ('',FG), (f"Goal: {m.get('goal') or '-'}", FG)]
        if m.get('reason'): out.append((f"  {m['reason']}",DIM))
        out.append(('Behaviour Tree:',HEADING))
        for depth,name in enumerate(m.get('branch') or ['-']):
            out.append((f"{'  '*depth}> {name}",FG))
        out.append(('Last navigation search:',HEADING))
        if 'path_found' in m:
            out.extend([(f"  {m['algorithm']}: {'route found' if m['path_found'] else 'NO ROUTE'}",GOOD if m['path_found'] else BAD),
                        (f"  Path length: {m['path_length']}",FG),
                        (f"  Nodes explored: {m['nodes_explored']}",FG),
                        (f"  Search time: {m['search_ms']:.2f} ms",FG)])
        else: out.append(('  -',DIM))
        out.append(('Puzzle:',HEADING))
        out.append((f"  {m.get('puzzle','Not started')}",FG))
        if 'puzzle_progress' in m: out.append((f"  Switches applied: {m['puzzle_progress']}",FG))
        if 'puzzle_world' in m: out.append((f"  World puzzle: {m['puzzle_world']}",FG))
        if 'puzzle_strategy' in m:
            out.extend([(f"  CSP: {m['puzzle_strategy']}",DIM),
                        (f"  {m['puzzle_assignments']} assignments, {m['puzzle_backtracks']} backtracks",DIM)])
        extras = [(k,m[k]) for k in ('keys','position','step') if k in m]
        if extras:
            out.append(('Agent:',HEADING))
            out.extend((f'  {k.capitalize()}: {v}',FG) for k,v in extras)
        out.append(('Recent actions:',HEADING))
        for e in reversed(self.events):
            out.append((f"  [{e['step']}] {e['source']}: {e['message']}",FG))
        return out
    def draw(self, surface, rect):
        """Wrap every text line within the inspector's available width."""
        if self._fonts is None:
            pygame.font.init()
            self._fonts = pygame.font.Font(None, 20)
        font = self._fonts
        surface.fill(BG, rect)
        left, right = rect.left + 10, rect.right - 10
        y = rect.top + 10
        line_height = font.get_linesize() + 2
        headings = {"AI Inspector", "Behaviour Tree:", "Last navigation search:",
                    "Puzzle:", "Agent:", "Recent actions:"}

        def wrapped(message):
            if not message:
                return [""]
            lines, current = [], ""
            for word in message.split():
                trial = (current + " " + word).strip()
                if font.size(trial)[0] <= right - left:
                    current = trial
                    continue
                if current:
                    lines.append(current)
                    current = ""
                while word and font.size(word)[0] > right - left:
                    n = len(word)
                    while n > 1 and font.size(word[:n])[0] > right - left:
                        n -= 1
                    lines.append(word[:n])
                    word = word[n:]
                current = word
            if current:
                lines.append(current)
            return lines or [""]

        old_clip = surface.get_clip()
        surface.set_clip(rect)
        try:
            for message, colour in self.lines():
                if message in headings and y > rect.top + 10:
                    y += 5
                for part in wrapped(message):
                    if y + line_height > rect.bottom - 8:
                        return
                    surface.blit(font.render(part, True, colour), (left, y))
                    y += line_height
        finally:
            surface.set_clip(old_clip)

if __name__ == '__main__':
    pygame.init()
    screen=pygame.display.set_mode((Inspector.WIDTH,620))
    panel=Inspector()
    panel.record(0,'Demo','Connect this panel to main.py for live game data')
    clock=pygame.time.Clock()
    running=True
    while running:
        for event in pygame.event.get():
            if event.type==pygame.QUIT or (event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE): running=False
        panel.draw(screen,screen.get_rect())
        pygame.display.flip()
        clock.tick(30)
    pygame.quit()
