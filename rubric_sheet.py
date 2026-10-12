"""
rubric_sheet.py: builds evaluation_rubric.md, a scoring sheet for six key runs.

Why it exists: my Python checks only test numbers (does it add up, are the bills there).
The rubric tests judgment. I score every cell myself (Pass / Partial / Fail plus one
sentence of evidence). This script only gathers the facts to look at, from the saved
logs in logs/final. It never scores anything. Run:  python3 rubric_sheet.py
"""

import calendar
import glob
import json
import re
from datetime import date
from pathlib import Path

from tools import get_calendar, get_recurring_expenses, get_spending_summary

ROOT = Path(__file__).parent
ALLOC = "How should I allocate this month's income?"
RUNS = [
    ("quiet", ALLOC), ("birthday", ALLOC), ("over_budget", ALLOC), ("drift", ALLOC),
    ("over_budget", "Can I afford a $2,500 laptop this month?"),
    ("over_budget", "Can I afford a $6,000 international vacation this month?"),
]
CRITERIA = [
    ("Priority alignment", "Did it protect what Maya values most, and did the stated priorities actually change the numbers (not just get mentioned)?"),
    ("Context awareness", "Did upcoming events or booked costs materially affect the decision?"),
    ("Historical reasoning", "Did it use relevant history (averages, same month last year, trends) appropriately?"),
    ("Transparency", "Did it say what Maya gives up, and by how much?"),
    ("Uncertainty", "Did it separate known costs from estimates or unknowns, and say what happens if an estimate is wrong?"),
]


def newest_logs():
    newest = {}
    for path in sorted(glob.glob(str(ROOT / "logs" / "final" / "*_*.json"))):  # names sort by time
        run = json.load(open(path))
        run["_file"] = Path(path).name
        newest[(run["scenario"], run["question"])] = run
    return newest


def step_of(run, tool):
    return next((s["step"] for s in run["steps"] if s.get("tool") == tool), None)


def lookup_line(run, tool, label):
    n = step_of(run, tool)
    return f"- {label}: " + (f"called at step {n}" if n else "**not called**")


def facts_for(run):
    d = str(ROOT / "data" / run["scenario"])
    answer = run["final_answer"] or ""
    lines = [lookup_line(run, "get_priorities", "priorities"), lookup_line(run, "get_calendar", "calendar"),
             lookup_line(run, "get_goals", "goals"), lookup_line(run, "get_spending_summary", "spending summary (6 months + same month last year)")]
    cites = re.search(r"last (year|december|october|july|august)|a year ago|same month", answer, re.I)
    lines.append("- the final answer mentions last year: " + ("yes" if cites else "**no**"))

    today = date.fromisoformat(run["today_in_scenario"])
    last_day = calendar.monthrange(today.year, today.month)[1]
    events = get_calendar(d, f"{today.year}-{today.month:02d}-01", f"{today.year}-{today.month:02d}-{last_day}")["events"]
    for e in events:
        if e["known_cost_usd"] is None:
            words = [w for w in re.findall(r"[a-z']+", e["title"].lower()) if len(w) >= 4]
            seen = any(w in answer.lower() for w in words)
            lines.append(f"- unknown-cost event \"{e['title']}\": " + ("mentioned in the answer" if seen else "**not mentioned**"))
        else:
            lines.append(f"- booked cost \"{e['title']}\" ${e['known_cost_usd']:,.0f}: counted in the answer's numbers? check the answer")

    if run["allocation"]:
        fixed = {i["name"] for i in get_recurring_expenses(d)["items"]}
        rows = get_spending_summary(d, 6)["categories"]
        year = get_spending_summary(d, 1)["categories"]
        changed = [f"  - {r['category']}: typical ${r['average_monthly_usd']:,.2f} -> allocated ${run['allocation'].get(r['category'], 0):,.2f}"
                   for r in rows if r["category"] not in fixed
                   and abs(run["allocation"].get(r["category"], 0) - r["average_monthly_usd"]) >= 50]
        lines.append("- categories changed from typical by $50 or more (did the answer explain each?):")
        lines += changed or ["  - none"]
        below = [f"  - {r['category']}: allocated ${run['allocation'].get(r['category'], 0):,.2f}, same month last year ${r['same_month_last_year_usd']:,.2f}"
                 for r in year if r["category"] not in fixed and r["same_month_last_year_usd"] is not None
                 and r["same_month_last_year_usd"] - run["allocation"].get(r["category"], 0) >= 100]
        lines.append("- categories at least $100 below the same month last year:")
        lines += below or ["  - none"]
    return lines


def main():
    logs = newest_logs()
    out = ["# Evaluation rubric (I score every cell myself)", "",
           "Scale: **Pass** = the information clearly changed the recommendation. **Partial** = used, but thinly, or only some of it. "
           "**Fail** = ignored, or contradicted. Do not give credit for merely *mentioning* a priority or calling a tool. "
           "Write one sentence of evidence per cell (a step number or a quote). The facts below only point to where to look.", ""]
    for number, (scenario, question) in enumerate(RUNS, 1):
        run = logs.get((scenario, question))
        if run is None:
            out += [f"## Run {number}: {scenario} (no saved log found)", ""]
            continue
        tools = [s["tool"] for s in run["steps"] if "tool" in s]
        out += [f"## Run {number}: {scenario} | {question}", "",
                f"Model {run['model']}, {run['steps_used']} steps, outcome {run['outcome']}, "
                f"{len(run['flags'])} check flag(s). Log: `logs/final/{run['_file']}`",
                f"Tools in order: {' > '.join(tools)}"]
        out += [f"Flags: {f}" for f in run["flags"]]
        out += ["", "Facts to look at:"] + facts_for(run)
        out += ["", "Final answer:", ""] + ["> " + line for line in (run["final_answer"] or "").split("```")[0].strip().splitlines()]
        out += ["", "| Criterion | What to look for | Score | One sentence of evidence |", "|---|---|---|---|"]
        out += [f"| {name} | {ask} |  |  |" for name, ask in CRITERIA] + [""]
    out += ["## Summary (fill in after scoring)", "", "| Run | Priority | Context | History | Transparency | Uncertainty |", "|---|---|---|---|---|---|"]
    out += [f"| {n}. {s}: {q[:40]} |  |  |  |  |  |" for n, (s, q) in enumerate(RUNS, 1)]
    (ROOT / "evaluation_rubric.md").write_text("\n".join(out) + "\n")
    print("Wrote evaluation_rubric.md with", len(RUNS), "runs")


if __name__ == "__main__":
    main()
