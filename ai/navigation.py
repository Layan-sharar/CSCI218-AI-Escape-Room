#Navigation interface for the ROGUEMIND game.



from ai.astar import astar_search


def find_path(grid, start, goal, blocked_cells=None,
              use_heuristic=True):
    #Calculate a route and return the route plus search statistics.
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
