"""
run_tests.py: runs the ten final questions and saves one log per run in logs/final/.

Why it exists: the logs are my evidence that the path varies (a quiet month should call
few tools, a crunch month many). The summary table at the end puts the tool sequences
side by side. Every run is a paid API call, so the ten runs are listed here, in one place.

Run:  venv/bin/python3 run_tests.py         (all ten)
      venv/bin/python3 run_tests.py 3 5     (only runs 3 and 5)
"""

import json
import sys

from agent import ROOT, load_settings, run_agent, show

LOG_DIR = ROOT / "logs" / "final"
ALLOCATION = "How should I allocate this month's income?"
RUNS = [
    ("quiet", ALLOCATION),
    ("birthday", ALLOCATION),
    ("over_budget", ALLOCATION),
    ("drift", ALLOCATION),
    ("quiet", "Can I afford a $400 weekend trip with friends this month?"),
    ("over_budget", "Can I afford a $300 night out with friends this month?"),
    ("quiet", "Can I afford a $25 lunch with a friend this month?"),    # small: should need little lookup
    ("quiet", "Can I afford a $2,500 laptop this month?"),              # large: should need more
    ("over_budget", "Can I afford a $2,500 laptop this month?"),        # same item as run 8, different month
    ("over_budget", "Can I afford a $6,000 international vacation this month?"),  # far beyond this month's cash
]


def run_one(number, model):
    """Run one question, print every step, and return one summary row."""
    scenario, question = RUNS[number - 1]
    print(f"\n{'=' * 72}\nRUN {number}: {scenario} | {question}\n{'=' * 72}")
    row = {"run": number, "scenario": scenario, "kind": "purchase" if question.startswith("Can I") else "allocation",
           "outcome": "crashed", "steps": 0, "tokens_in": 0, "tokens_out": 0, "flags": 0, "tools": []}
    try:
        for event in run_agent(scenario, question, model, log_dir=LOG_DIR):
            show(event)
            if event["type"] == "action":
                row["tools"].append(event["tool"])
            elif event["type"] == "checks":
                row["flags"] = len(event["flags"])
            elif event["type"] == "done":
                row.update(outcome=event["outcome"], steps=event["steps"], log=event["log_path"],
                           tokens_in=event["tokens"]["input"], tokens_out=event["tokens"]["output"])
    except Exception as problem:  # one bad run must not stop the others; say so loudly
        print(f"\n!!! RUN {number} CRASHED: {type(problem).__name__}: {problem}")
    return row


def print_summary(rows):
    print(f"\n{'=' * 72}\nSUMMARY (the tool sequence is the evidence that the path varies)\n{'=' * 72}")
    for r in rows:
        print(f"\nRun {r['run']}: {r['scenario']} / {r['kind']}: {r['outcome']}, {r['steps']} steps, "
              f"{r['tokens_in']:,} in / {r['tokens_out']:,} out, {r['flags']} flag(s)")
        print("  tools:", " > ".join(r["tools"]) or "(none)")


def main():
    args = sys.argv[1:]
    numbers = [int(a) for a in args if a.isdigit()]
    if len(numbers) != len(args) or any(n < 1 or n > len(RUNS) for n in numbers):
        sys.exit(f"Usage: venv/bin/python3 run_tests.py [run numbers from 1 to {len(RUNS)}]")
    numbers = numbers or list(range(1, len(RUNS) + 1))
    model = load_settings()
    print(f"Model: {model} | runs: {numbers} | logs go to {LOG_DIR}")
    rows = [run_one(n, model) for n in numbers]
    print_summary(rows)
    if numbers == list(range(1, len(RUNS) + 1)):  # only a full set overwrites the summary file
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        (LOG_DIR / "summary.json").write_text(json.dumps(rows, indent=2) + "\n")
        print(f"\nSummary saved to {LOG_DIR / 'summary.json'}")


if __name__ == "__main__":
    main()
