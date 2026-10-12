"""
checks.py: the four checks my CODE runs on the model's allocation after it answers.

Why it exists: a model can write a tidy allocation that does not actually work
(it adds to the wrong total, or quietly shrinks the rent). These checks catch that.
They only FLAG problems. They never fix, rebalance, or change the allocation.
The model never sees this file or its results.

Each check returns a plain-English flag. An empty list means every check passed.
"""

import json
import re

from tools import get_balance, get_recurring_expenses

INCOME_TOLERANCE_USD = 1.00   # check 1: allowed rounding gap
BILL_TOLERANCE_USD = 0.01     # check 2: allowed gap for a fixed bill (cents)
UNASSIGNED_LIMIT = 0.10       # check 4: unassigned may be at most 10% of income


def extract_allocation(final_text):
    """Find the ```json block in the final answer.
    Returns (allocation, problem). (None, None) means there was no block at all,
    which is normal for a purchase question."""
    blocks = re.findall(r"```json\s*(.*?)```", final_text, re.DOTALL)
    if not blocks:
        return None, None
    try:
        data = json.loads(blocks[-1])  # the answer ends with the block, so take the last one
    except json.JSONDecodeError:
        return None, "the allocation block is not valid JSON"
    if not isinstance(data, dict) or not data:
        return None, "the allocation block must be a non-empty JSON object"
    for name, amount in data.items():
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            return None, f"the amount for '{name}' is not a number: {amount!r}"
    return data, None


def check_allocation(allocation, income_usd, fixed_bills):
    """Run the four checks. `fixed_bills` maps each fixed bill's name to its real monthly amount."""
    flags = []
    unfunded = allocation.get("unfunded_usd")
    spending_total = sum(v for k, v in allocation.items() if k != "unfunded_usd")
    unfunded_allowed = sum(fixed_bills.values()) > income_usd

    # Check 1: the sum. If an unfunded line is allowed, its amount is subtracted first.
    counted = spending_total - unfunded if (unfunded is not None and unfunded_allowed) else spending_total
    if abs(counted - income_usd) > INCOME_TOLERANCE_USD:
        flags.append(f"FLAG sum: allocation counts as ${counted:,.2f} but expected income is "
                     f"${income_usd:,.2f} (off by ${counted - income_usd:+,.2f})")

    # Check 2: every fixed bill is present, at its real amount.
    for name, real in fixed_bills.items():
        if name not in allocation:
            flags.append(f"FLAG fixed bill: '{name}' (${real:,.2f}) is missing from the allocation")
        elif allocation[name] < real - BILL_TOLERANCE_USD:
            flags.append(f"FLAG fixed bill: '{name}' is ${allocation[name]:,.2f} but the real amount is ${real:,.2f}")

    # Check 3: an unfunded line is allowed only if fixed bills alone exceed income.
    if unfunded is not None and not unfunded_allowed:
        flags.append(f"FLAG unfunded: 'unfunded_usd' is ${unfunded:,.2f}, but fixed bills "
                     f"(${sum(fixed_bills.values()):,.2f}) fit within income (${income_usd:,.2f})")

    # Check 4: unassigned money may not be more than 10% of income.
    unassigned = allocation.get("unassigned", 0)
    if unassigned > UNASSIGNED_LIMIT * income_usd:
        flags.append(f"FLAG unassigned: ${unassigned:,.2f} is {unassigned / income_usd:.1%} of income "
                     f"(limit {UNASSIGNED_LIMIT:.0%})")
    return flags


def check_scenario(data_dir, allocation):
    """Load the real income and fixed bills for this scenario, then run the checks."""
    income = get_balance(data_dir)["income_expected_this_month_usd"]
    bills = {item["name"]: item["amount_usd"]
             for item in get_recurring_expenses(data_dir)["items"] if item["kind"] == "fixed_bill"}
    return check_allocation(allocation, income, bills)
