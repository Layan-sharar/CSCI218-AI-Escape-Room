"""Navigation interface for the ROGUEMIND game.

Other project modules should call find_path() from this file rather than
depending on the internal details of the A* implementation.
"""

from ai.astar import astar_search


def find_path(grid, start, goal, blocked_cells=None,
              use_heuristic=True):
    """Calculate a route and return the route plus search statistics.

    The returned dictionary can be passed to Person E's inspector. The
    value in result["path"] is directly compatible with movement.set_route().
    Replanning uses the same function with the latest grid and blocked cells.
    """
    return astar_search(
        grid,
        start,
        goal,
        blocked_cells=blocked_cells,
        use_heuristic=use_heuristic
    )


def find_new_path(grid, current_position, goal, blocked_cells=None,
                  use_heuristic=True):
    """Recalculate a route after the map or obstacle state changes.

    This deliberately calls find_path again; callers should supply the
    updated grid and/or updated blocked_cells.
    """
    return find_path(
        grid,
        current_position,
        goal,
        blocked_cells=blocked_cells,
        use_heuristic=use_heuristic
    )
