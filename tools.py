"""
tools.py: the fact-only tools the budget agent can call.

Why it exists: the model decides WHAT to look up; these functions do the looking
up and the arithmetic. Every tool returns plain facts (numbers, dates, what the
user said). No tool ever says what something means, such as "affordable" or
"cut this". That judgment is the model's job.

Every tool takes `data_dir` first. My code fills it in from the scenario name;
the model never sees or chooses it. "Today" always comes from scenario.json,
never from the computer's clock.
"""

import json
from datetime import date
from pathlib import Path

MAX_ROWS = 50  # get_transactions never returns more rows than this


# ---------- Small helpers ----------

def _load(data_dir, name):
    """Read one JSON file from the scenario folder."""
    return json.loads((Path(data_dir) / f"{name}.json").read_text())


def _today(data_dir):
    """The fictional 'today' for this scenario."""
    return date.fromisoformat(_load(data_dir, "scenario")["today"])


def _parse_date(text):
    """Turn 'YYYY-MM-DD' into a date, or return None if it is not a valid date."""
    try:
        return date.fromisoformat(str(text))
    except ValueError:
        return None


def _month_number(d):
    """Count months from year 0, so two months can be subtracted."""
    return d.year * 12 + (d.month - 1)


def _categories(data_dir):
    return sorted({t["category"] for t in _load(data_dir, "transactions")})


# ---------- The tools ----------

def get_balance(data_dir):
    """Checking balance today, income received so far, and income still expected."""
    balance = _load(data_dir, "balance")
    still_expected = balance["income_expected_this_month_usd"] - balance["income_received_this_month_usd"]
    balance["income_still_expected_this_month_usd"] = round(still_expected, 2)
    return balance


def get_recurring_expenses(data_dir):
    """Every recurring bill and subscription, whether it is paid yet this month, and totals."""
    today = _today(data_dir)
    items = []
    for item in _load(data_dir, "recurring"):
        row = dict(item)
        row["paid_this_month"] = item["due_day_of_month"] <= today.day
        items.append(row)

    def total(rows):
        return round(sum(r["amount_usd"] for r in rows), 2)

    return {
        "as_of_date": today.isoformat(),
        "items": items,
        "total_fixed_bill_usd": total(r for r in items if r["kind"] == "fixed_bill"),
        "total_subscription_usd": total(r for r in items if r["kind"] == "subscription"),
        "total_still_due_this_month_usd": total(r for r in items if not r["paid_this_month"]),
    }


def get_transactions(data_dir, category, start_date, end_date):
    """Past spending in one category (or "all") between two dates, with count and total."""
    if category != "all" and category not in _categories(data_dir):
        return {"error": f"unknown category '{category}'", "valid_categories": ["all"] + _categories(data_dir)}
    start, end = _parse_date(start_date), _parse_date(end_date)
    if start is None or end is None:
        return {"error": "dates must look like YYYY-MM-DD, for example 2026-09-01"}
    if start > end:
        return {"error": "start_date is after end_date"}

    rows = [t for t in _load(data_dir, "transactions")
            if (category == "all" or t["category"] == category)
            and start <= date.fromisoformat(t["date"]) <= end]
    shown = rows[-MAX_ROWS:]  # if there are too many, keep the most recent
    return {
        "category": category, "start_date": start.isoformat(), "end_date": end.isoformat(),
        "transaction_count": len(rows),
        "total_usd": round(sum(t["amount_usd"] for t in rows), 2),
        "rows_shown": len(shown),
        "rows": shown,
    }


def get_category_average(data_dir, category, num_months):
    """Average monthly spend in one category over the last N FULL months (this month excluded)."""
    if category not in _categories(data_dir):
        return {"error": f"unknown category '{category}'", "valid_categories": _categories(data_dir)}
    try:
        n = int(num_months)
    except (TypeError, ValueError):
        return {"error": "num_months must be a whole number from 1 to 12"}
    if not 1 <= n <= 12:
        return {"error": "num_months must be a whole number from 1 to 12"}

    current = _month_number(_today(data_dir))
    months = [f"{m // 12}-{m % 12 + 1:02d}" for m in range(current - n, current)]
    totals = {m: 0.0 for m in months}  # a month with no spending counts as $0
    for t in _load(data_dir, "transactions"):
        if t["category"] == category and t["date"][:7] in totals:
            totals[t["date"][:7]] += t["amount_usd"]

    values = list(totals.values())
    return {
        "category": category, "num_months": n,
        "first_month": months[0], "last_month": months[-1],
        "average_monthly_usd": round(sum(values) / n, 2),
        "lowest_month_usd": round(min(values), 2),
        "highest_month_usd": round(max(values), 2),
        "monthly_totals": [{"month": m, "total_usd": round(v, 2)} for m, v in totals.items()],
    }


def get_calendar(data_dir, start_date, end_date):
    """Calendar events that overlap the given dates."""
    start, end = _parse_date(start_date), _parse_date(end_date)
    if start is None or end is None:
        return {"error": "dates must look like YYYY-MM-DD, for example 2026-12-01"}
    if start > end:
        return {"error": "start_date is after end_date"}
    events = [e for e in _load(data_dir, "calendar")
              if date.fromisoformat(e["start_date"]) <= end and date.fromisoformat(e["end_date"]) >= start]
    return {"start_date": start.isoformat(), "end_date": end.isoformat(),
            "event_count": len(events), "events": events}


def get_goals(data_dir):
    """Savings and investing goals, with the amount remaining and months left (this month included)."""
    today = _today(data_dir)
    goals = []
    for goal in _load(data_dir, "goals"):
        row = dict(goal)
        row["remaining_usd"] = None
        row["months_left_including_this_one"] = None
        if goal["target_usd"] is not None:
            row["remaining_usd"] = round(goal["target_usd"] - goal["saved_so_far_usd"], 2)
        if goal["deadline"] is not None:
            months = _month_number(date.fromisoformat(goal["deadline"])) - _month_number(today) + 1
            row["months_left_including_this_one"] = max(months, 0)
        goals.append(row)
    return {"as_of_date": today.isoformat(), "goals": goals}


def get_priorities(data_dir):
    """What the user SAID they care about, word for word. Not a ranking of what to cut."""
    return _load(data_dir, "priorities")


def sum_amounts(data_dir, amounts_usd):
    """Add up a list of numbers (negative numbers subtract). Pure arithmetic."""
    if not isinstance(amounts_usd, list):
        return {"error": "amounts_usd must be a list of numbers, for example [2400, 350, -100]"}
    for a in amounts_usd:
        if isinstance(a, bool) or not isinstance(a, (int, float)):
            return {"error": f"not a number: {a!r}. amounts_usd must contain only numbers"}
    return {"count": len(amounts_usd), "total_usd": round(sum(amounts_usd), 2)}


# ---------- Looking up a tool by name ----------

TOOLS = {
    "get_balance": get_balance,
    "get_recurring_expenses": get_recurring_expenses,
    "get_transactions": get_transactions,
    "get_category_average": get_category_average,
    "get_calendar": get_calendar,
    "get_goals": get_goals,
    "get_priorities": get_priorities,
    "sum_amounts": sum_amounts,
}


def run_tool(data_dir, name, args):
    """Run one tool by name. Never crashes: problems come back as {"error": ...}."""
    if name not in TOOLS:
        return {"error": f"unknown tool '{name}'", "valid_tools": sorted(TOOLS)}
    if not isinstance(args, dict):
        return {"error": 'arguments must be a JSON object, for example {"category": "groceries"}'}
    try:
        return TOOLS[name](data_dir, **args)
    except TypeError as problem:  # missing, extra, or misspelled argument names
        return {"error": f"wrong arguments for {name}: {problem}"}
