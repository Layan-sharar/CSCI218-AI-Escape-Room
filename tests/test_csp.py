import itertools

import pytest

from ai.csp import CSP, Constraint, solve
from puzzles.switch_puzzle import (
    SWITCHES,
    compare_strategies,
    default_puzzle,
    impossible_puzzle,
    solve_puzzle,
)

STRATEGIES = [
    {"mrv": False, "forward_checking": False},
    {"mrv": True, "forward_checking": False},
    {"mrv": False, "forward_checking": True},
    {"mrv": True, "forward_checking": True},
]


def satisfies_all(csp, assignment):
    return all(c.check(*[assignment[v] for v in c.scope]) for c in csp.constraints)


def brute_force_solutions(csp):
    found = []
    for values in itertools.product(*[csp.domains[v] for v in csp.variables]):
        assignment = dict(zip(csp.variables, values))
        if satisfies_all(csp, assignment):
            found.append(assignment)
    return found


# ---- tests for the solver on its own ----------------------------------------

def two_colour_chain():
    return CSP(
        variables=["A", "B", "C"],
        domains={"A": [1, 2], "B": [1, 2], "C": [1, 2]},
        constraints=[
            Constraint(("A", "B"), lambda a, b: a != b, "A differs from B"),
            Constraint(("B", "C"), lambda b, c: b != c, "B differs from C"),
        ],
    )


def two_colour_triangle():
    csp = two_colour_chain()
    csp.constraints.append(Constraint(("A", "C"), lambda a, c: a != c, "A differs from C"))
    return csp


@pytest.mark.parametrize("options", STRATEGIES)
def test_engine_solves_a_generic_csp_that_is_not_the_switch_puzzle(options):
    result = solve(two_colour_chain(), **options)

    assert result.success
    assert satisfies_all(two_colour_chain(), result.solution)


@pytest.mark.parametrize("options", STRATEGIES)
def test_engine_reports_failure_for_an_unsatisfiable_csp(options):
    result = solve(two_colour_triangle(), **options)

    assert not result.success
    assert result.solution is None


@pytest.mark.parametrize("options", STRATEGIES)
def test_engine_fails_immediately_when_a_variable_has_an_empty_domain(options):
    csp = CSP(variables=["A"], domains={"A": []}, constraints=[])

    result = solve(csp, **options)

    assert not result.success


@pytest.mark.parametrize("options", STRATEGIES)
def test_engine_handles_a_constraint_over_three_variables(options):
    csp = CSP(
        variables=["X", "Y", "Z"],
        domains={"X": [0, 1], "Y": [0, 1], "Z": [0, 1]},
        constraints=[Constraint(("X", "Y", "Z"), lambda x, y, z: x + y + z == 2, "exactly two are 1")],
    )

    result = solve(csp, **options)

    assert result.success
    assert sum(result.solution.values()) == 2


@pytest.mark.parametrize("options", STRATEGIES)
def test_engine_applies_a_single_variable_constraint(options):
    csp = CSP(
        variables=["A", "B"],
        domains={"A": [0, 1], "B": [0, 1]},
        constraints=[Constraint(("A",), lambda a: a == 1, "A must be 1")],
    )

    result = solve(csp, **options)

    assert result.solution["A"] == 1


def test_solving_twice_gives_the_same_answer_and_does_not_change_the_csp():
    csp = default_puzzle().csp
    domains_before = {v: list(d) for v, d in csp.domains.items()}

    first = solve(csp, mrv=True, forward_checking=True)
    second = solve(csp, mrv=True, forward_checking=True)

    assert first.solution == second.solution
    assert csp.domains == domains_before


def test_stats_are_recorded_for_every_run():
    result = solve(default_puzzle().csp, mrv=True, forward_checking=True)

    assert result.stats.assignments > 0
    assert result.stats.backtracks >= 0
    assert result.stats.runtime_seconds >= 0


# ---- tests for the switch puzzle --------------------------------------------

def test_puzzle_has_four_to_five_switches_and_written_rules():
    puzzle = default_puzzle()

    assert 4 <= len(puzzle.switches) <= 5
    assert puzzle.switches == SWITCHES
    assert len(puzzle.rules) == len(puzzle.csp.constraints)
    assert all(isinstance(rule, str) and rule for rule in puzzle.rules)


def test_puzzle_has_exactly_one_solution_so_the_demo_is_repeatable():
    csp = default_puzzle().csp

    solutions = brute_force_solutions(csp)

    assert solutions == [
        {"RED": True, "BLUE": False, "GREEN": True, "YELLOW": True, "WHITE": True}
    ]


@pytest.mark.parametrize("options", STRATEGIES)
def test_solver_returns_the_assignment_that_satisfies_every_rule(options):
    puzzle = default_puzzle()

    result = solve(puzzle.csp, **options)

    assert result.success
    assert satisfies_all(puzzle.csp, result.solution)


@pytest.mark.parametrize("options", STRATEGIES)
def test_solver_rejects_the_impossible_puzzle(options):
    puzzle = impossible_puzzle()

    assert brute_force_solutions(puzzle.csp) == []
    assert not solve(puzzle.csp, **options).success


def test_solve_puzzle_returns_solved_flag_and_switch_settings_for_the_world():
    result = solve_puzzle(default_puzzle())

    assert result.solved is True
    assert result.settings == {
        "RED": True, "BLUE": False, "GREEN": True, "YELLOW": True, "WHITE": True,
    }
    assert result.stats.assignments > 0


def test_solve_puzzle_with_no_argument_uses_the_default_puzzle():
    assert solve_puzzle().solved is True


def test_solve_puzzle_reports_not_solved_with_no_settings_for_the_impossible_puzzle():
    result = solve_puzzle(impossible_puzzle())

    assert result.solved is False
    assert result.settings is None


# ---- tests comparing plain and improved search ------------------------------

def test_improved_search_makes_fewer_assignments_than_plain_backtracking():
    puzzle = default_puzzle()

    plain = solve(puzzle.csp)
    improved = solve(puzzle.csp, mrv=True, forward_checking=True)

    assert improved.stats.assignments < plain.stats.assignments
    assert improved.stats.backtracks < plain.stats.backtracks


def test_improved_search_is_no_worse_on_the_impossible_puzzle():
    puzzle = impossible_puzzle()

    plain = solve(puzzle.csp)
    improved = solve(puzzle.csp, mrv=True, forward_checking=True)

    assert improved.stats.assignments <= plain.stats.assignments


def test_compare_strategies_runs_all_four_and_they_agree_on_the_answer():
    comparison = compare_strategies(default_puzzle())

    assert list(comparison) == ["plain", "mrv", "forward_checking", "mrv+forward_checking"]
    assert len({tuple(sorted(r.settings.items())) for r in comparison.values()}) == 1
    assert all(r.solved for r in comparison.values())


def test_mrv_alone_makes_fewer_assignments_than_plain_backtracking():
    puzzle = default_puzzle()

    plain = solve(puzzle.csp)
    with_mrv = solve(puzzle.csp, mrv=True)

    assert with_mrv.stats.assignments < plain.stats.assignments


def test_forward_checking_alone_makes_fewer_assignments_than_plain_backtracking():
    puzzle = default_puzzle()

    plain = solve(puzzle.csp)
    with_fc = solve(puzzle.csp, forward_checking=True)

    assert with_fc.stats.assignments < plain.stats.assignments


def doomed_csp_with_unrelated_variables_in_the_middle():
    """A and B can never both be satisfied, and C and D sit between them but do not matter."""
    return CSP(
        variables=["A", "C", "D", "B"],
        domains={"A": [1], "C": [1, 2, 3], "D": [1, 2, 3], "B": [1]},
        constraints=[Constraint(("A", "B"), lambda a, b: a != b, "A differs from B")],
    )


def test_forward_checking_gives_up_as_soon_as_a_domain_is_emptied():
    csp = doomed_csp_with_unrelated_variables_in_the_middle()

    plain = solve(csp)
    with_fc = solve(csp, forward_checking=True)

    assert not plain.success and not with_fc.success
    assert with_fc.stats.assignments == 1
    assert plain.stats.assignments > 9


def test_mrv_goes_straight_to_the_variable_with_no_legal_values():
    csp = doomed_csp_with_unrelated_variables_in_the_middle()

    with_mrv = solve(csp, mrv=True)

    assert not with_mrv.success
    assert with_mrv.stats.assignments == 2


def test_comparison_table_lists_every_strategy_with_its_search_effort():
    from puzzles.switch_puzzle import format_comparison

    table = format_comparison(default_puzzle())
    lines = table.splitlines()

    assert lines[0].startswith("| Strategy")
    assert len(lines) == 2 + 4
    for name in ("plain", "mrv", "forward_checking", "mrv+forward_checking"):
        assert any(line.startswith(f"| {name} ") for line in lines)
