"""Constraint satisfaction solver: variables, domains, rules and backtracking search.

solve(csp) is plain backtracking. Two extras can be turned on:
  mrv=True               choose the variable with the fewest legal values first
                         (on a tie, the one in the most rules with unassigned variables)
  forward_checking=True  after each choice, remove values that no longer work from the
                         other variables, and stop early if one of them has none left
"""

import time
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass(frozen=True)
class Constraint:
    scope: tuple
    check: Callable[..., bool]
    description: str = ""


@dataclass
class CSP:
    variables: list
    domains: dict
    constraints: list = field(default_factory=list)


@dataclass
class SolveStats:
    assignments: int = 0
    backtracks: int = 0
    runtime_seconds: float = 0.0


@dataclass
class SolveResult:
    success: bool
    solution: Optional[dict]
    stats: SolveStats


def solve(csp: CSP, mrv: bool = False, forward_checking: bool = False) -> SolveResult:
    stats = SolveStats()
    started = time.perf_counter()

    domains = {v: list(csp.domains[v]) for v in csp.variables}
    by_variable = {v: [c for c in csp.constraints if v in c.scope] for v in csp.variables}
    assignment: dict = {}

    def consistent(var: str) -> bool:
        """Check every rule that involves var and has all of its variables assigned."""
        return all(
            c.check(*[assignment[v] for v in c.scope])
            for c in by_variable[var]
            if all(v in assignment for v in c.scope)
        )

    def legal_values(var: str) -> list:
        if forward_checking:
            return domains[var]
        legal = []
        for value in domains[var]:
            assignment[var] = value
            if consistent(var):
                legal.append(value)
            del assignment[var]
        return legal

    def choose_variable() -> str:
        unassigned = [v for v in csp.variables if v not in assignment]
        if not mrv:
            return unassigned[0]

        def key(v: str):
            open_constraints = sum(
                1 for c in by_variable[v] if any(u != v and u not in assignment for u in c.scope)
            )
            return (len(legal_values(v)), -open_constraints)

        return min(unassigned, key=key)

    def prune(c: Constraint, target: str, removed: list) -> None:
        """Remove the values of target that would break rule c (its other variables are already assigned)."""
        for value in list(domains[target]):
            assignment[target] = value
            ok = c.check(*[assignment[v] for v in c.scope])
            del assignment[target]
            if not ok:
                domains[target].remove(value)
                removed.append((target, value))

    def prune_neighbours(var: str) -> tuple:
        """Forward checking. Returns the removed (variable, value) pairs, and False if a variable ran out of values."""
        removed = []
        for c in by_variable[var]:
            open_vars = [v for v in c.scope if v not in assignment]
            if len(open_vars) == 1:
                prune(c, open_vars[0], removed)
                if not domains[open_vars[0]]:
                    return removed, False
        return removed, True

    def restore(removed: list) -> None:
        for target, value in removed:
            domains[target].append(value)

    def search() -> bool:
        if len(assignment) == len(csp.variables):
            return True
        var = choose_variable()
        for value in list(domains[var]):
            stats.assignments += 1
            assignment[var] = value
            if consistent(var):
                if forward_checking:
                    removed, domains_ok = prune_neighbours(var)
                    if domains_ok and search():
                        return True
                    restore(removed)
                elif search():
                    return True
            del assignment[var]
            stats.backtracks += 1
        return False

    if forward_checking:
        for c in csp.constraints:
            if len(c.scope) == 1:
                prune(c, c.scope[0], [])

    success = all(domains[v] for v in csp.variables) and search()
    stats.runtime_seconds = time.perf_counter() - started
    return SolveResult(success, dict(assignment) if success else None, stats)
