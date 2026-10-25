"""runs.jsonl -> report.md, overall, by question type and by path; and two runs side by side (EV-12, EV-13, EV-20).

    python -m neuro_rag.eval.report eval/results/<folder>
    python -m neuro_rag.eval.report eval/results/<new> --compare eval/results/<old>
"""
import argparse
import json
from pathlib import Path

from neuro_rag.eval.run import JUDGED_FOR_CORRECTNESS

SCORE = {"correct": 1.0, "partial": 0.5, "wrong": 0.0}
COLUMNS = ["runs", "correctness", "faithful", "retrieval hit", "cites expected", "not covered",
           "p50 s", "p95 s", "$ per answer"]
PATHS = ["papers", "papers_rewritten", "none"]
PATH_COLUMNS = ["runs", "share", "correctness", "p50 s", "p95 s", "$ per answer"]
COMPARED = ["correctness", "faithful", "retrieval hit", "cites expected", "not covered", "p95 s", "$ per answer"]


def load_runs(folder: Path) -> list[dict]:
    with open(folder / "runs.jsonl", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _mean(values) -> float | None:
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def _percentile(values, p) -> float | None:
    values = sorted(values)
    return values[max(0, int(round(p * len(values))) - 1)] if values else None


def _latency(run: dict) -> float:
    """The whole ask for a corrective run; retrieval plus generation for the others (EV-18)."""
    return run["total_s"] if "total_s" in run else run["retrieval_s"] + run["generation_s"]


def scores(runs: list[dict]) -> dict:
    """Every score for a group of runs; None where no run in the group has that measure."""
    ok = [r for r in runs if not r["error"]]
    times = [_latency(r) for r in ok]
    return {
        "runs": len(runs),
        "correctness": _mean(SCORE.get(r.get("correctness")) for r in ok),
        "faithful": _mean(None if r.get("faithful") is None else float(r["faithful"]) for r in ok),
        "retrieval hit": _mean(None if r.get("retrieval_hit") is None else float(r["retrieval_hit"]) for r in ok),
        "cites expected": _mean(None if r.get("cites_expected") is None else float(r["cites_expected"]) for r in ok),
        "not covered": _mean(None if r.get("not_covered") is None else float(r["not_covered"]) for r in ok),
        "p50 s": _percentile(times, 0.5),
        "p95 s": _percentile(times, 0.95),
        "$ per answer": _mean(r.get("cost_usd") for r in ok),
    }


def by_type(runs: list[dict]) -> dict[str, dict]:
    """'all' first (multilingual excluded: English only), then each question type."""
    groups = {"all (excl. multilingual)": [r for r in runs if not r["type"].startswith("multilingual")]}
    for t in sorted({r["type"] for r in runs}):
        groups[t] = [r for r in runs if r["type"] == t]
    return {name: scores(group) for name, group in groups.items()}


def by_path(runs: list[dict]) -> dict[str, dict]:
    """Each path's runs, share and scores; multilingual and failed runs left out, as in the overall row (EV-20)."""
    ok = [r for r in runs if not r["error"] and not r["type"].startswith("multilingual")]
    rows = {}
    for path in PATHS:
        group = [r for r in ok if r.get("path") == path]
        if group:
            rows[path] = {**scores(group), "share": len(group) / len(ok)}
    return rows


def rerouted(runs: list[dict]) -> list[dict]:
    """Answerable questions that weren't answered on the first search, run by run (EV-20)."""
    picked = [r for r in runs if not r["error"] and r.get("expected_behavior") in JUDGED_FOR_CORRECTNESS
              and r.get("path") not in (None, "papers")]
    return sorted(picked, key=lambda r: (r["id"], r["repeat"]))


def _fmt(column: str, value) -> str:
    if value is None:
        return "–"
    if column == "runs":
        return str(value)
    if column == "share":
        return f"{value:.0%}"
    if column in ("p50 s", "p95 s"):
        return f"{value:.1f}"
    if column == "$ per answer":
        return f"{value:.4f}"
    return f"{value:.2f}"


def _table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return "\n".join(lines + ["| " + " | ".join(row) + " |" for row in rows])


def build_report(runs: list[dict], meta: dict) -> str:
    errors = sum(1 for r in runs if r["error"])
    judge_errors = sum(1 for r in runs if r.get("judge_error"))
    head = [f"# Eval report: {meta.get('system', '')}", "",
            f"- system model: {meta.get('system_model')}; judge model: {meta.get('judge_model')}; "
            f"index: {meta.get('index')}",
            f"- {len(runs)} runs ({meta.get('repeats')} repeats, {meta.get('workers')} at a time); "
            f"{errors} failed; {judge_errors} not judged", "",
            "Correctness: correct 1, partial 0.5, wrong 0. Rates are fractions of the runs each measure "
            "applies to; – means it applies to none. Latency is retrieval plus generation; for the corrective system, the whole question.", ""]
    rows = [[name] + [_fmt(c, s[c]) for c in COLUMNS] for name, s in by_type(runs).items()]
    report = "\n".join(head) + _table(["questions"] + COLUMNS, rows) + "\n"
    if any("path" in r for r in runs):  # the corrective system (row 7a); other reports are unchanged
        paths = [[path] + [_fmt(c, s[c]) for c in PATH_COLUMNS] for path, s in by_path(runs).items()]
        listed = [[r["id"], str(r["repeat"]), r["path"], r.get("query") or "–", r.get("correctness") or "–"]
                  for r in rerouted(runs)]
        report += ("\n## By path\n\n" + _table(["path"] + PATH_COLUMNS, paths) + "\n"
                   "\n## Answerable questions not answered on the first search\n\n"
                   + _table(["id", "repeat", "path", "rewritten query", "correctness"], listed) + "\n")
    return report


def build_comparison(new: list[dict], old: list[dict], new_name: str, old_name: str) -> str:
    """Each score side by side with its difference, overall and by type (EV-13)."""
    a, b = by_type(old), by_type(new)
    rows = []
    for group in a.keys() | b.keys():
        for c in COMPARED:
            va, vb = a.get(group, {}).get(c), b.get(group, {}).get(c)
            if va is None and vb is None:
                continue
            diff = "–" if va is None or vb is None else f"{vb - va:+.2f}" if c not in ("$ per answer",) else f"{vb - va:+.4f}"
            rows.append((group != "all (excl. multilingual)", group, c, _fmt(c, va), _fmt(c, vb), diff))
    rows.sort()
    return (f"# Comparison: {new_name} vs {old_name}\n\n"
            + _table(["questions", "score", old_name, new_name, "difference"], [list(r[1:]) for r in rows]) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the eval report.")
    parser.add_argument("folder", type=Path)
    parser.add_argument("--compare", type=Path, help="an earlier results folder to compare with")
    args = parser.parse_args()

    runs = load_runs(args.folder)
    meta_path = args.folder / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    report = build_report(runs, meta)
    (args.folder / "report.md").write_text(report, encoding="utf-8")
    print(report)
    if args.compare:
        comparison = build_comparison(runs, load_runs(args.compare), args.folder.name, args.compare.name)
        (args.folder / f"compare_{args.compare.name}.md").write_text(comparison, encoding="utf-8")
        print(comparison)


if __name__ == "__main__":
    main()
