"""
baseline.py: the plain if-statement version of the budget agent. No model, no API calls.

Why it exists: it is the control. Running it on the same four months shows where the
language model earns its place and where simple rules do just as well.

The rules (deliberately simple, but fair: it uses the real 6-month averages):
  1. Pay every recurring bill and subscription in full.
  2. Give every everyday category its 6-month average.
  3. All that is left goes to savings. (It never looks at goals, the calendar, priorities,
     last year, or trends, because a fixed rule has no way to weigh them.)
  4. A purchase is affordable (YES) if its price is no more than what is left after the
     bills, the everyday averages and a 20% savings share of income. Otherwise NO.

Its allocation goes through the same five checks, and is printed next to what the agent
recommended in logs/final. Run:  python3 baseline.py
"""

import glob
import json
import re
from pathlib import Path

from checks import check_scenario
from tools import get_balance, get_recurring_expenses, get_spending_summary

ROOT = Path(__file__).parent
SCENARIOS = ["quiet", "birthday", "over_budget", "drift"]
SAVINGS_SHARE = 0.20   # a purchase may not touch the 20% of income reserved for savings
MONTHS = 6             # how many full months the everyday averages cover
GOAL_NAMES = ("savings", "roth_ira")


def baseline_plan(data_dir):
    """Returns (allocation, what_is_left_for_a_purchase)."""
    income = get_balance(data_dir)["income_expected_this_month_usd"]
    plan = {item["name"]: item["amount_usd"] for item in get_recurring_expenses(data_dir)["items"]}  # rule 1
    for row in get_spending_summary(data_dir, MONTHS)["categories"]:                                 # rule 2
        if row["category"] not in plan and row["category"] not in GOAL_NAMES:
            plan[row["category"]] = row["average_monthly_usd"]
    left = income - sum(plan.values())
    plan["savings"] = round(max(left, 0), 2)                                                          # rule 3
    return plan, left - SAVINGS_SHARE * income


def newest_logs():
    """The newest agent log for each (scenario, question) in logs/final."""
    newest = {}
    for path in sorted(glob.glob(str(ROOT / "logs" / "final" / "*_*.json"))):  # file names sort by time
        run = json.load(open(path))
        newest[(run["scenario"], run["question"])] = run
    return newest


def agent_verdict(answer):
    found = re.search(r"\b(YES|TIGHT|NO)\b", (answer or "")[:40].upper())
    return found.group(1) if found else "?"


def main():
    out = []
    logs = newest_logs()
    plans = {s: baseline_plan(str(ROOT / "data" / s)) for s in SCENARIOS}

    out.append("ALLOCATION: baseline vs agent (only categories that differ by $1 or more)")
    for s in SCENARIOS:
        plan, _ = plans[s]
        flags = check_scenario(str(ROOT / "data" / s), plan)
        agent = next((r["allocation"] for (sc, q), r in logs.items() if sc == s and q.startswith("How should")), None)
        out.append(f"\n== {s} ==")
        out.append(f"baseline checks: {len(flags)} flag(s)")
        out += [f"  {f}" for f in flags]
        if agent is None:
            out.append("  (no agent allocation saved for this scenario)")
            continue
        out.append(f"  {'category':22}{'baseline':>11}{'agent':>11}{'difference':>12}")
        for name in sorted(set(plan) | set(agent)):
            b, a = plan.get(name, 0), agent.get(name, 0)
            if abs(a - b) >= 1:
                out.append(f"  {name:22}{b:>11,.2f}{a:>11,.2f}{a - b:>+12,.2f}")

    out.append("\n\nPURCHASES: baseline vs agent")
    out.append(f"  {'scenario':12}{'price':>9}  {'left for a purchase':>20}  {'baseline':9}{'agent':8}question")
    for (s, q), run in sorted(logs.items()):
        price = re.search(r"\$([\d,]+)", q)
        if not q.startswith("Can I") or not price or s not in plans:
            continue
        cost, left = float(price.group(1).replace(",", "")), plans[s][1]
        out.append(f"  {s:12}{cost:>9,.0f}  {left:>20,.2f}  {'YES' if cost <= left else 'NO':9}{agent_verdict(run['final_answer']):8}{q}")

    text = "\n".join(out)
    print(text)
    (ROOT / "logs" / "baseline_comparison.txt").write_text(text + "\n")
    print("\nSaved to logs/baseline_comparison.txt")


if __name__ == "__main__":
    main()
