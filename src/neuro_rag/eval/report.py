from math import ceil

VERDICT_SCORE = {"correct": 1.0, "partial": 0.5, "wrong": 0.0}

COLUMNS = ["questions", "runs", "correctness", "faithful", "paper@5", "page@5",
           "cites expected", "not covered", "cites papers", "p50 s", "p95 s", "$ per run"]


def judged(value: dict | None) -> bool:
    """A judge result that exists and isn't a judge error."""
    return value is not None and "error" not in value


def rate(values: list) -> str:
    """Mean of the values that aren't None, 2 decimals; – when there are none."""
    values = [float(v) for v in values if v is not None]
    return f"{sum(values) / len(values):.2f}" if values else "–"


def percentile(values: list[float], p: int) -> str:
    """Nearest-rank percentile, 1 decimal; – when there are no values."""
    if not values:
        return "–"
    return f"{sorted(values)[ceil(p / 100 * len(values)) - 1]:.1f}"


def row(group: str, records: list[dict]) -> str:
    ok = [r for r in records if r["error"] is None]  # failed runs count in "runs" only
    seconds = [r["search_s"] + r["answer_s"] for r in ok]
    costs = [r["cost_usd"] for r in ok]
    cells = [
        group,
        str(len(records)),
        rate([VERDICT_SCORE[r["correctness"]["verdict"]] if judged(r["correctness"]) else None for r in ok]),
        rate([r["faithfulness"]["faithful"] if judged(r["faithfulness"]) else None for r in ok]),
        rate([r["paper_hit"] for r in ok]),
        rate([r["page_hit"] for r in ok]),
        rate([r["cites_expected"] for r in ok]),
        rate([r["not_covered"] for r in ok]),
        rate([r["cites_papers"] for r in ok]),
        percentile(seconds, 50),
        percentile(seconds, 95),
        f"{sum(costs) / len(costs):.4f}" if costs else "–",
    ]
    return "| " + " | ".join(cells) + " |"


def build_report(records: list[dict], name: str) -> str:
    # 1. header
    failed = sum(r["error"] is not None for r in records)
    judge_failed = sum(
        isinstance(r[key], dict) and "error" in r[key]
        for r in records for key in ("correctness", "faithfulness")
    )
    total_cost = sum(r["cost_usd"] or 0 for r in records)
    lines = [
        f"# Eval report: {name}",
        "",
        f"{len(records)} runs, {failed} failed, {judge_failed} judge calls failed, ${total_cost:.2f} total",
        "",
    ]

    # 2. table: all, then one row per type, sorted by name
    lines.append("| " + " | ".join(COLUMNS) + " |")
    lines.append("|" + "---|" * len(COLUMNS))
    lines.append(row("all", records))
    for type_ in sorted({r["type"] for r in records}):
        lines.append(row(type_, [r for r in records if r["type"] == type_]))

    # 3. not correct, with the judge's reason
    lines += ["", "## Not correct", ""]
    for r in records:
        c = r["correctness"]
        if judged(c) and c["verdict"] != "correct":
            lines.append(f"- {r['id']} r{r['repeat']} {c['verdict']}: {c['reason']}")

    # 4. unfaithful, with the first unsupported claim
    lines += ["", "## Unfaithful", ""]
    for r in records:
        f = r["faithfulness"]
        if judged(f) and not f["faithful"]:
            lines.append(f"- {r['id']} r{r['repeat']}: \"{f['unsupported_claim']}\"")

    return "\n".join(lines) + "\n"
