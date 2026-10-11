"""
generate_data.py: creates the SYNTHETIC (made-up) data the budget agent reads.

Why it exists: the agent must never see real financial data. This script builds
one fictional person ("Maya") and four test months, each designed to push the
agent down a different path. A fixed random seed means every run writes exactly
the same files, so results can be reproduced.

Run:     python3 generate_data.py
Output:  data/<scenario>/ with 7 JSON files in each folder.
"""

import json
import random
from datetime import date
from pathlib import Path

SEED = 42
DATA_DIR = Path(__file__).parent / "data"
HISTORY_MONTHS = 12  # full months of history before "today"

# ---------- Maya's facts (the same in every scenario) ----------

PAYCHECK_USD = 4350.00          # paid on each payday below
PAYDAYS = [1, 15]
INCOME_EXPECTED_USD = 8700.00   # take-home pay per month
CHECKING_BUFFER_USD = 2100.00   # money already in checking before this month

# (name, amount_usd, due_day_of_month, kind)
RECURRING = [
    ("rent", 2400.00, 1, "fixed_bill"),
    ("student_loans", 350.00, 5, "fixed_bill"),
    ("internet", 70.00, 8, "fixed_bill"),
    ("orthodontic_payment", 169.00, 10, "fixed_bill"),
    ("phone", 70.00, 12, "fixed_bill"),
    ("utilities", 120.00, 18, "fixed_bill"),
    ("car_insurance", 180.00, 20, "fixed_bill"),
    ("renters_insurance", 15.00, 25, "fixed_bill"),
    ("solidcore", 258.00, 3, "subscription"),
    ("spotify", 6.99, 7, "subscription"),
    ("applecare", 20.00, 14, "subscription"),
    ("icloud", 2.99, 21, "subscription"),
    ("streaming", 15.49, 27, "subscription"),
]
ORTHODONTIC_FINAL_PAYMENT = date(2027, 2, 10)

# Money moved to goals each month, on the day after the second paycheck.
# (category, amount_usd, day_of_month)
GOAL_TRANSFERS = [
    ("savings", 1667.00, 16),     # same names as the goals in goals.json
    ("roth_ira", 625.00, 16),
]

# category: (monthly_low_usd, monthly_high_usd, purchases_per_month, merchants)
FLEXIBLE = {
    "groceries": (450, 550, 6, ["Whole Foods", "Sprouts", "Trader Joe's", "Farmers market"]),
    "eating_out": (243, 297, 7, ["Sweetgreen", "Cava", "Sushi bar", "Coffee shop", "Thai kitchen"]),
    "shopping": (200, 600, 4, ["Sephora", "Target", "Amazon - supplements", "Lululemon", "Ulta"]),
    "transport": (130, 190, 4, ["Shell", "Chevron", "Costco gas"]),
    "entertainment": (50, 110, 2, ["AMC", "Concert tickets", "Bowling"]),
    "health": (20, 80, 1, ["CVS copay", "Walgreens"]),
}

PRIORITIES = [
    "Saving $20,000 this year is my main money goal.",
    "Contributing to my Roth IRA every month is a priority.",
    "Other investing, like stocks or crypto, matters less to me than experiences and memories with friends.",
    "Eating clean matters to me. I don't want to cut back on grocery quality.",
    "Solidcore is important for my health, and I'd keep it if I can.",
    "I try to keep eating out under $400 a month.",
]

BROKERAGE_BALANCE_USD = 4200.00

# Drift scenario: eating out starts here and grows 5% each month.
DRIFT_START_USD = 220.00
DRIFT_RATE = 0.05


def event(start, end, title, known_cost_usd=None, known_cost_note=None):
    """One calendar entry. Costs are filled in only when they are known facts."""
    return {"start_date": start, "end_date": end, "title": title,
            "known_cost_usd": known_cost_usd, "known_cost_note": known_cost_note}


def spend(day, category, amount, description):
    """One past transaction (a date, a category, an amount, a description)."""
    return {"date": day, "category": category, "amount_usd": amount, "description": description}


# ---------- What is different in each scenario ----------

SCENARIOS = {
    "quiet": {
        "today": date(2026, 7, 2),
        "calendar": [event("2026-07-16", "2026-07-16", "Book club at Priya's")],
        "extra_transactions": [],
        "eating_out_drift": False,
    },
    "birthday": {
        "today": date(2026, 10, 3),
        "calendar": [
            event("2026-10-18", "2026-10-18", "My birthday"),
            event("2026-10-24", "2026-10-24", "Book club at Priya's"),
        ],
        "extra_transactions": [
            spend("2025-10-15", "shopping", 180.00, "Birthday outfit - Reformation"),
            spend("2025-10-18", "eating_out", 260.00, "Birthday dinner - Uchi"),
        ],
        "eating_out_drift": False,
    },
    "over_budget": {
        "today": date(2026, 12, 2),
        "calendar": [
            event("2026-12-18", "2026-12-20", "Sam and Jordan's wedding (Denver)",
                  1350.00, "flight $520 and hotel $830, due before the trip"),
            event("2026-12-24", "2026-12-26", "Holidays at Mom's"),
        ],
        "extra_transactions": [
            spend("2025-12-08", "gifts", 120.00, "Holiday gifts - Nordstrom"),
            spend("2025-12-14", "gifts", 95.00, "Holiday gifts - Etsy"),
            spend("2025-12-20", "gifts", 185.00, "Holiday gifts - Amazon"),
            spend("2026-05-23", "gifts", 200.00, "Wedding gift - Zola registry"),
        ],
        "eating_out_drift": False,
    },
    "drift": {
        "today": date(2026, 8, 3),
        "calendar": [event("2026-08-13", "2026-08-13", "Book club at Priya's")],
        "extra_transactions": [],
        "eating_out_drift": True,
    },
}


# ---------- Builders: each one makes the contents of one file ----------

def month_starts(today):
    """First day of each month: 12 full history months, then the current month."""
    current = today.year * 12 + (today.month - 1)
    return [date(m // 12, m % 12 + 1, 1) for m in range(current - HISTORY_MONTHS, current + 1)]


def build_transactions(rng, today, scenario):
    """Every expense from the first history month up to and including today."""
    rows = []
    for index, first in enumerate(month_starts(today)):
        for name, amount, due_day, _kind in RECURRING:
            rows.append(spend(first.replace(day=due_day).isoformat(), name, amount, "Autopay - " + name))
        for category, amount, day in GOAL_TRANSFERS:
            rows.append(spend(first.replace(day=day).isoformat(), category, amount, "Transfer - " + category))
        for category, (low, high, count, merchants) in FLEXIBLE.items():
            if category == "eating_out" and scenario["eating_out_drift"]:
                total = DRIFT_START_USD * (1 + DRIFT_RATE) ** index * rng.uniform(0.98, 1.02)
            else:
                total = rng.uniform(low, high)
            weights = [rng.uniform(0.5, 1.5) for _ in range(count)]
            for weight in weights:
                day = first.replace(day=rng.randint(1, 28)).isoformat()
                amount = round(total * weight / sum(weights), 2)
                rows.append(spend(day, category, amount, rng.choice(merchants)))
    rows += scenario["extra_transactions"]
    rows = [r for r in rows if r["date"] <= today.isoformat()]
    return sorted(rows, key=lambda r: r["date"])


def build_recurring(today):
    """Recurring bills and subscriptions. Only the orthodontic payment has an end date."""
    items = []
    for name, amount, due_day, kind in RECURRING:
        item = {"name": name, "amount_usd": amount, "due_day_of_month": due_day, "kind": kind,
                "final_payment_date": None, "payments_remaining": None}
        if name == "orthodontic_payment":
            first_month = today.year * 12 + today.month - 1
            if today.day > due_day:
                first_month += 1  # this month's payment has already gone out
            last_month = ORTHODONTIC_FINAL_PAYMENT.year * 12 + ORTHODONTIC_FINAL_PAYMENT.month - 1
            item["final_payment_date"] = ORTHODONTIC_FINAL_PAYMENT.isoformat()
            item["payments_remaining"] = last_month - first_month + 1
        items.append(item)
    return items


def build_balance(today, transactions):
    """Checking balance today = buffer + paychecks so far this month - spending so far this month."""
    month_prefix = today.isoformat()[:7]
    received = PAYCHECK_USD * sum(1 for d in PAYDAYS if d <= today.day)
    spent = sum(r["amount_usd"] for r in transactions if r["date"].startswith(month_prefix))
    return {"as_of_date": today.isoformat(),
            "checking_balance_usd": round(CHECKING_BUFFER_USD + received - spent, 2),
            "income_received_this_month_usd": received,
            "income_expected_this_month_usd": INCOME_EXPECTED_USD}


def build_goals(today, transactions):
    """Goal progress is added up from the actual transfers made this calendar year."""
    def total_this_year(category):
        year = str(today.year)
        return round(sum(r["amount_usd"] for r in transactions
                         if r["category"] == category and r["date"].startswith(year)), 2)

    return [
        {"name": "savings", "target_usd": 20000.00, "saved_so_far_usd": total_this_year("savings"),
         "deadline": "2026-12-31", "planned_monthly_usd": 1667.00},
        {"name": "roth_ira", "target_usd": 7500.00, "saved_so_far_usd": total_this_year("roth_ira"),
         "deadline": "2026-12-31", "planned_monthly_usd": 625.00},
        {"name": "brokerage_investing", "target_usd": None, "saved_so_far_usd": BROKERAGE_BALANCE_USD,
         "deadline": None, "planned_monthly_usd": None},
    ]


def write_json(path, contents):
    path.write_text(json.dumps(contents, indent=2) + "\n")


def main():
    for offset, (name, scenario) in enumerate(SCENARIOS.items()):
        rng = random.Random(SEED + offset)  # one fixed seed per scenario
        today = scenario["today"]
        folder = DATA_DIR / name
        folder.mkdir(parents=True, exist_ok=True)

        transactions = build_transactions(rng, today, scenario)
        write_json(folder / "scenario.json", {"today": today.isoformat()})
        write_json(folder / "balance.json", build_balance(today, transactions))
        write_json(folder / "recurring.json", build_recurring(today))
        write_json(folder / "transactions.json", transactions)
        write_json(folder / "calendar.json", scenario["calendar"])
        write_json(folder / "goals.json", build_goals(today, transactions))
        write_json(folder / "priorities.json", {"stated_priorities": PRIORITIES})
        print(f"Wrote data/{name}/  ({len(transactions)} transactions, today = {today})")


if __name__ == "__main__":
    main()
