"""
narrate.py: turns one tool call and its result into a plain-English sentence.

Why it exists: the live demo prints raw JSON, which is hard to follow. These sentences
are written by MY CODE from the real tool result, not by the model, so they cannot be
invented. They are for display only; the model never sees them and they change nothing.
"""


def _usd(value):
    return f"${value:,.2f}"


def narrate(tool, args, result):
    """One sentence saying what this step looked up and what came back."""
    if isinstance(result, dict) and "error" in result:
        return f"The call to {tool} came back with an error: {result['error']}"
    try:
        if tool == "get_balance":
            return (f"Looked up the balance: {_usd(result['checking_balance_usd'])} in checking, and "
                    f"{_usd(result['income_received_this_month_usd'])} of the "
                    f"{_usd(result['income_expected_this_month_usd'])} expected this month has arrived.")
        if tool == "get_recurring_expenses":
            return (f"Looked up recurring bills: {len(result['items'])} items. Fixed bills total "
                    f"{_usd(result['total_fixed_bill_usd'])}, subscriptions {_usd(result['total_subscription_usd'])}, "
                    f"and {_usd(result['total_still_due_this_month_usd'])} is still due this month.")
        if tool == "get_transactions":
            return (f"Looked at {result['transaction_count']} past purchases in '{result['category']}' from "
                    f"{result['start_date']} to {result['end_date']}, totalling {_usd(result['total_usd'])}.")
        if tool == "get_category_average":
            return (f"Checked '{result['category']}' over the last {result['num_months']} full months: it averages "
                    f"{_usd(result['average_monthly_usd'])} a month (lowest {_usd(result['lowest_month_usd'])}, "
                    f"highest {_usd(result['highest_month_usd'])}).")
        if tool == "get_spending_summary":
            return (f"Listed what {len(result['categories'])} categories typically cost per month over "
                    f"{result['first_month']} to {result['last_month']}, with what each cost in "
                    f"{result['same_month_last_year']} for comparison.")
        if tool == "get_calendar":
            if not result["events"]:
                return f"Checked the calendar from {result['start_date']} to {result['end_date']}: nothing planned."
            parts = [e["title"] + (f" (known cost {_usd(e['known_cost_usd'])})" if e["known_cost_usd"] is not None
                                   else " (no known cost)") for e in result["events"]]
            return (f"Checked the calendar from {result['start_date']} to {result['end_date']}: "
                    f"{result['event_count']} event(s): " + "; ".join(parts) + ".")
        if tool == "get_goals":
            parts = [f"{g['name']} {_usd(g['remaining_usd'])} to go" if g["remaining_usd"] is not None
                     else f"{g['name']} (no target)" for g in result["goals"]]
            return "Looked up her goals: " + "; ".join(parts) + "."
        if tool == "get_priorities":
            return f"Read the {len(result['stated_priorities'])} priorities she stated in her own words."
        if tool == "sum_amounts":
            return f"Added up {result['count']} numbers with the adding tool: the total is {_usd(result['total_usd'])}."
    except (KeyError, TypeError):
        pass
    return f"Ran {tool}."
