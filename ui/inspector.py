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
        self.update(puzzle='Solution found' if result.solved else 'No solution',
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
        out.append(('Last A* search:',HEADING))
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
        if self._fonts is None:
            pygame.font.init()
            self._fonts = pygame.font.Font(None,20)
        surface.fill(BG,rect)
        y = rect.top+10
        for message,colour in self.lines():
            if y > rect.bottom-18: break
            # Clip long log entries to panel width, rather than overflowing into the game.
            while message and self._fonts.size(message)[0] > rect.width-20:
                message = message[:-1]
            surface.blit(self._fonts.render(message,True,colour),(rect.left+10,y))
            y+=18

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
