"""EV-11: does the judge agree with a person? Two steps.

    python -m neuro_rag.eval.judge_check sheet eval/results/<folder>
        -> writes <folder>/judge_check.csv: 20 random judged runs, judge verdicts hidden.
           Fill in human_correctness (correct / partial / wrong, or leave empty if
           there is no reference) and human_faithful (yes / no, or empty if nothing is cited).

    python -m neuro_rag.eval.judge_check score eval/results/<folder>
        -> compares your grades with the judge's; passes at 16 of 20 or more.
"""
import argparse
import csv
import random
from pathlib import Path

from neuro_rag.eval.report import load_runs

SAMPLE = 20
PASS = 16
FIELDS = ["id", "repeat", "question", "reference_answer", "answer", "cited_sources",
          "human_correctness", "human_faithful"]


def judged(runs: list[dict]) -> list[dict]:
    return [r for r in runs if not r["error"] and not r.get("judge_error")
            and (r.get("correctness") is not None or r.get("faithful") is not None)]


def write_sheet(folder: Path, references: dict[str, str | None], seed: int = 0) -> Path:
    runs = judged(load_runs(folder))
    sample = random.Random(seed).sample(runs, min(SAMPLE, len(runs)))
    path = folder / "judge_check.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for r in sample:
            cited = "\n\n".join(f"[{n}] " + "\n".join(t) for n, t in sorted(r.get("cited_chunks", {}).items()))
            writer.writerow({"id": r["id"], "repeat": r["repeat"], "question": r["question"],
                             "reference_answer": references.get(r["id"]) or "", "answer": r["answer"],
                             "cited_sources": cited, "human_correctness": "", "human_faithful": ""})
    return path


def agreement(folder: Path) -> tuple[int, int, list[str]]:
    """(runs where the person and the judge agree, runs compared, one line per disagreement)."""
    judge = {(r["id"], r["repeat"]): r for r in load_runs(folder)}
    agree, total, disagreements = 0, 0, []
    with open(folder / "judge_check.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            r = judge[(row["id"], int(row["repeat"]))]
            human_c = row["human_correctness"].strip().lower() or None
            human_f = {"yes": True, "no": False}.get(row["human_faithful"].strip().lower())
            same = human_c == r.get("correctness") and human_f == r.get("faithful")
            total += 1
            agree += same
            if not same:
                disagreements.append(f"{row['id']} #{row['repeat']}: you {human_c}/{human_f}, "
                                     f"judge {r.get('correctness')}/{r.get('faithful')}")
    return agree, total, disagreements


def main() -> None:
    from neuro_rag.eval.run import load_questions

    parser = argparse.ArgumentParser(description="Check the judge against a person (EV-11).")
    parser.add_argument("step", choices=["sheet", "score"])
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    if args.step == "sheet":
        references = {q.id: q.reference_answer for q in load_questions()}
        print(f"fill in: {write_sheet(args.folder, references)}")
    else:
        agree, total, disagreements = agreement(args.folder)
        print("\n".join(disagreements))
        print(f"EV-11: judge agrees with you on {agree}/{total}: {'PASS' if agree >= PASS else 'FAIL'}")


if __name__ == "__main__":
    main()
