import csv

from experiments.run_trials import SCENARIOS, main, run_csp_trials, run_search_trials


def by_scenario(rows):
    return {(r["scenario"], r["algorithm"]): r for r in rows}


def test_every_scenario_runs_with_both_algorithms():
    rows = run_search_trials(repeats=2)
    assert len(rows) == 2 * len(SCENARIOS)
    assert {(r["scenario"], r["algorithm"]) for r in rows} == {
        (s, a) for s in SCENARIOS for a in ("A*", "UCS")
    }


def test_astar_matches_ucs_optimality_and_never_explores_more():
    rows = by_scenario(run_search_trials(repeats=1))
    for name in SCENARIOS:
        astar, ucs = rows[(name, "A*")], rows[(name, "UCS")]
        assert astar["found"] == ucs["found"]
        assert astar["cost"] == ucs["cost"]
        assert astar["nodes_explored"] <= ucs["nodes_explored"]


def test_heuristic_prunes_on_an_open_straight_route():
    rows = by_scenario(run_search_trials(repeats=1))
    assert rows[("open_30x30_straight", "A*")]["nodes_explored"] * 10 < rows[("open_30x30_straight", "UCS")]["nodes_explored"]


def test_replan_takes_a_longer_route_and_impossible_map_fails():
    rows = by_scenario(run_search_trials(repeats=1))
    assert rows[("replan_after_block", "A*")]["path_length"] > rows[("direct_route", "A*")]["path_length"]
    assert rows[("no_route", "A*")]["found"] is False


def test_csp_rows_cover_both_puzzles_and_mrv_fc_beats_plain():
    rows = {(r["puzzle"], r["strategy"]): r for r in run_csp_trials(repeats=2)}
    assert len(rows) == 8
    assert all(r["solved"] for (p, _), r in rows.items() if p == "default")
    assert not any(r["solved"] for (p, _), r in rows.items() if p == "impossible")
    for puzzle in ("default", "impossible"):
        assert rows[(puzzle, "mrv+forward_checking")]["assignments"] < rows[(puzzle, "plain")]["assignments"]


def test_main_writes_readable_csvs(tmp_path, capsys):
    main(["--repeats", "1", "--out", str(tmp_path)])
    with (tmp_path / "astar_vs_ucs.csv").open() as f:
        search = list(csv.DictReader(f))
    with (tmp_path / "csp_strategies.csv").open() as f:
        puzzle = list(csv.DictReader(f))
    assert len(search) == 2 * len(SCENARIOS)
    assert search[0]["algorithm"] == "A*"
    assert len(puzzle) == 8
    assert "astar_vs_ucs.csv" in capsys.readouterr().out
