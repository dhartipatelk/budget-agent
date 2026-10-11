# CLAUDE.md: Budget Agent (BUAN 6V99 mini-project)

Read this file fully before doing anything. If anything here conflicts with a request I make in chat, tell me about the conflict before acting.

## What this project is

A budgeting agent, built from scratch in plain Python for a university course. I lose track of what I can afford when events compete for the same money. The agent investigates a (fictional) user's spending history, recurring bills, calendar, goals, and stated priorities, then recommends ONE tradeoff with a reason. It answers two kinds of question with the same loop:

1. "How should I allocate this month's income?"
2. "Can I afford this specific purchase?"

All data is synthetic. Never use, ask for, or generate real bank data. The README must say the data is synthetic.

## Project status (this is a LIVE file)

Due: Monday Oct 12, 2026. Solo, 20% of the course grade. Graded on: whether it is a real agent (see the hard requirements below), the repo (README, structure, real commit history, no secrets), a five-minute presentation with a live demo, and whether I can explain every file and how I verified it. No UI is required for this assignment.

Done so far:

- Step 1: plan and file structure agreed (Oct 11, 2026). Decisions recorded below.
- Step 2 PLAN agreed (Oct 11, 2026). See "Step 2 plan" below. `generate_data.py` is NOT written yet.

Not done yet: build steps 2 to 8.

Next session starts here: write `generate_data.py` exactly as in "Step 2 plan" below, run it, then show me a sample of each file so I can read the output before committing.

### Step 2 plan (agreed, not yet written)

- Fixed seed: `random.seed(42)`. Never uses the real date.
- One fictional person ("Maya") in all four scenarios; each scenario is a different "today" with 12 months of history before it. Each folder is self-contained with all 7 files.
- Income: $4,200/month, paid $2,100 on the 1st and $2,100 on the 15th.
- Fixed bills (`fixed_bill`): rent $1,450, car payment $320, car insurance $145, phone $65, internet $60 (total $2,040).
- Subscriptions (`subscription`): streaming $16, music $11, gym $40 (total $67).
- Typical flexible spend (with about ±10% random noise): groceries ~$380, transport (gas) ~$140, eating out ~$220, shopping ~$150, entertainment ~$80.
- Goals: emergency fund ($6,000 target, ~$3,200 saved, $400/month); Roth IRA ($200/month).
- Priorities (user's own words): "Emergency fund comes first." "I'd rather keep seeing friends than invest more right now." "I try to keep eating out under $350 a month."

| Folder | Today | What is different | What it should force |
|---|---|---|---|
| `quiet/` | 2026-07-02 | Nothing; about $500 slack | Few tool calls, short answer |
| `birthday/` | 2026-10-03 | Calendar: "My birthday" Oct 18. Last October's history has a $260 dinner and $180 shopping | Model looks back at last year and sets money aside |
| `over_budget/` | 2026-12-02 | Friend's wedding in Denver (flight $380 + hotel $420 listed on the event) plus holiday gifts (~$300 last December); about $575 over | Model must cut and name the cost |
| `drift/` | 2026-08-03 | Eating out rises 5%/month, ~$180 to ~$310; never passes $350 | Model notices the trend by comparing averages |

Files per folder: `scenario.json` (today), `balance.json`, `recurring.json`, `transactions.json` (~300 rows: date, category, amount, description), `calendar.json`, `goals.json`, `priorities.json`. All flat records, units and dates in field names. No scenario labels or hints in any file.

Decisions made along the way:

1. **`sum_amounts` tool added.** The model must never add numbers itself, but it has to compare totals (for example bills + event + goals vs income). This tool only adds, so it has one right answer and stays fact-only.
2. **Tool arguments are written as JSON**, for example `ACTION: get_transactions({"category": "eating_out", "start_date": "2026-09-01", "end_date": "2026-09-30"})`. Parsed with `json.loads`, never `eval`. Simpler and safer than parsing Python-style arguments.
3. **One ACTION per reply.** The code uses only the first ACTION line and ignores anything after it, so the model cannot invent a tool result. If this happens in a trace, show it to me.
4. **Allocation covers the WHOLE month's expected income** (Option A), including fixed bills, subscriptions, goals, events, and an `unassigned` line. The code checks the sum equals expected monthly income within $1 (rounding). Simpler to check, and it catches a forgotten bill.
5. **429 retry uses the Anthropic SDK's built-in retry** (set to 3 retries, which uses backoff) instead of hand-written retry code. A 401 is caught and gives a clear "bad API key" message.
6. **Final run logs are committed** in `logs/` as evidence the path varies (synthetic data, no key). Throwaway runs go in `logs/scratch/`, which is gitignored (add this to `.gitignore` when the loop is built).
7. **System prompt lives in `prompts.py`**, separate from the loop, because it is long text that gets tuned often and this keeps `agent.py` small.
8. **Runs planned:** the allocation question on all four months, plus a purchase question on the quiet and over-budget months (6 runs). Shows both question types and a short vs long path.
9. **Model:** cheapest current Haiku-class model. Believed to be `claude-haiku-5-5`, but VERIFY on the Models overview page at docs.claude.com before putting it in `.env`.
10. **Optional tools skipped** (`get_spending_trend`, `get_past_decisions`) because of the deadline. Drift can be found by comparing `get_category_average` over 3 vs 6 months.
11. **The scenario folder is bound by the code, never a model argument.** Tools receive the data folder from my code; the model never sees or chooses it.
12. **Allocation checks live in `checks.py`**, a separate small file, because there are four checks (see "The final answer and the math check").
13. **Recurring items have a `kind` field: `fixed_bill` or `subscription`.** Only `fixed_bill` items (rent, car payment, insurance) must appear at their full amount. Cancelling a subscription is a legitimate tradeoff, so it is not flagged.
14. **Purchase verdicts are yes / tight / no**, with "essentials" defined (see "The final answer and the math check"). "No" depends on essentials and stated priorities, not arithmetic alone, so it stays a real judgment that an if-statement could not make.
15. **A $350 eating-out limit is in the priorities.** The drift scenario "never breaches a limit," so a limit must exist for drift to mean anything.
16. **A transport (gas) category exists in transactions**, so the "transport needed for work" essential has data behind it.
17. **The wedding event lists its known costs; the birthday does not.** Booked prices are facts. For the birthday, the model has to dig through last year's history, so the two paths differ.

Open questions: (anything I still need to ask my professor)

### End-of-session rule

When I say I am finished for the day, update this file before we stop: move finished items to "Done so far", note what comes next, record any design decisions and any problems found, and keep the file index below accurate. Never put the API key or any real data in this file. When I start a new session, read this file first and tell me where we left off.

### File index

Keep this list current so a fresh session knows what each file is for. (Fill in as files are created.)

- `CLAUDE.md`: project instructions and live status (this file).
- `.gitignore`: keeps `.env`, `venv/`, `__pycache__/` out of git.
- `requirements.txt`: Python packages (`anthropic`, `python-dotenv`, and their dependencies). No frameworks.

## Who I am and how to work with me

I am a student and I must be able to explain every file to my class. I am not an expert programmer.

- Keep files small. Add a short comment at the top of each file saying what it does and why it exists.
- Explain what you are about to do before you do it. Do not run commands I have not read.
- If you make a design choice that I did not ask for, say so and say why.
- If you think my approach is wrong, say so. I want your judgment, not just agreement.
- Build ONE step at a time and stop so I can read and commit. Do not build the whole project in one go.
- Before writing any code, give me your plan and file structure and flag anything in this file you would do differently.

## What counts as an agent here (hard requirements)

This is the course test. Everything below is graded.

1. MY OWN Python code makes the API call to the language model (the Anthropic SDK, called from a file in this repo). No platform, no custom GPT, no Claude Project.
2. The path must VARY. The next step depends on what the last step found. A quiet month should take few tool calls and a crunch month many. If every run calls the same tools in the same order, the design is wrong.
3. There must be real JUDGMENT that an if-statement could not capture.
4. TOOLS RETURN FACTS ONLY. The MODEL makes the call.
5. NO FRAMEWORK. No LangChain, LangGraph, CrewAI, or similar. Plain Python: a loop, an API call, a parser, and tool functions.
6. The loop has a hard step cap, because every step is a paid API call.
7. No secrets in the repo, ever.

## The loop (build it this way)

The model replies in plain text, and my code reads the first word:

- `ACTION: tool_name({"arg": "value"})` means: run this tool and give me the result. Arguments are JSON. One ACTION per reply; anything after the first ACTION line is ignored.
- `FINAL: answer` means: I am done.

My code does the rest: parse, run the tool, append the result to the conversation, repeat. The scenario data folder is passed to the tools by my code, never by the model.

Settings, defined as named constants at the top of the file:

- `MAX_STEPS = 25`. This is a starting value. I will adjust it after reading real traces. If a run hits the cap while still making steady progress, raise it. If it is looping on the same call, fix the tool descriptions instead.
- `MAX_TOKENS = 2000`. Too low silently cuts the answer off.
- The model name comes from the `.env` file (`MODEL_NAME`), not hard-coded, so I can swap models without editing code. Default to the cheapest current Haiku-class model. Check Anthropic's current docs for the exact model name rather than guessing from memory. Only move to a stronger model if the cheap one's judgment on the over-budget month is clearly weak.

Required behaviors:

- Parse tool calls safely. Never use `eval()` or `exec()` on model output.
- Retry with a short backoff on HTTP 429 (use the SDK's built-in retry, 3 retries). Give a clear message on 401 (bad key). Do not crash on one bad call.
- Print each step inside the loop (what the model decided to call, and what came back). These printed steps are my live demo.
- Log every run to a file: the question, each tool call and result, the final answer, step count, and token usage. I will use these logs to prove the path varies.
- The loop should `yield` each step (generator style) so a terminal or a web page could display it later. No UI is needed now.
- Add this line to the system prompt: "Only look up what you need to answer the question. Do not call every tool."

## Tools (facts only)

Each tool is a small function that reads the synthetic JSON files and returns small, flat JSON with explicit units and dates in the field names (for example {"category": "eating_out", "month": "2026-09", "total_usd": 412.50}). No deeply nested structures. Each tool's description in the system prompt must say WHEN it is useful, because the model chooses tools from the descriptions.

- `get_balance()`: current balance, income received so far this month, and expected total income for the month.
- `get_recurring_expenses()`: rent, subscriptions, car payment, car insurance, etc, with due dates. Each item has `kind`: `fixed_bill` or `subscription`.
- `get_transactions(category, start_date, end_date)`: what was actually spent, filtered.
- `get_category_average(category, num_months)`: typical spend in a category over past months.
- `get_calendar(start_date, end_date)`: upcoming events such as birthdays and trips.
- `get_goals()`: savings and investing goals, deadlines, and progress.
- `get_priorities()`: the user's STATED priorities (for example "emergency fund first, social life over investing"). It returns what the user said, not a ranking of what to cut.
- `sum_amounts(amounts_usd)`: adds a list of numbers (negative numbers subtract) and returns the total. Pure arithmetic, so the model never adds in its head.

Skipped because of the deadline: `get_spending_trend(category)`, `get_past_decisions()`.

### Tool rules

- Tools do arithmetic and lookups with one right answer. They never say what something means.
- A tool may report "you have $340 left after fixed bills." It may NOT say "you can afford this" or "cut eating out."
- DO NOT write `is_affordable()`, `calculate_allocation()`, `decide_what_to_do()`, `get_recommended_budget()`, `get_safe_to_spend()`, or anything like them. That moves the judgment into code and turns the agent into a script. A previous example in class (`assess_model()`) was deleted for exactly this reason.
- Arithmetic belongs in code, not in the model. The model should never be asked to add up numbers itself.

## The final answer and the math check

For allocation questions, the model ends with:

- a short explanation of the tradeoff and what it costs me, and
- a small allocation block as JSON (for example {"eating_out": 250, "groceries": 400}), so my code can parse it and sum it.

My code then sums the allocation and compares it to income. If it does not add up, the code FLAGS the mismatch visibly. The code must never silently fix or rebalance it. The point is to catch an agent that produces a tidy allocation that does not actually work.

The allocation covers the WHOLE month's expected income (from `get_balance()`), not just what is left after bills. Allocation keys for recurring items must use the same names that `get_recurring_expenses()` returns. The checks live in `checks.py`, and each one only FLAGS, never fixes:

1. **Sum check:** the allocation total equals expected monthly income, within $1.
2. **Fixed bill check:** every `fixed_bill` item appears in the allocation at its real amount. Flag any that are missing or reduced. (`subscription` items are not checked, because cancelling one is a valid tradeoff.)
3. **Unfunded check:** an `unfunded_usd` line is allowed ONLY if fixed bills alone exceed income. If it appears when fixed bills fit within income, flag it. When it is allowed, the sum check becomes: allocation total minus `unfunded_usd` equals income, within $1.
4. **Unassigned check:** flag `unassigned` if it is more than 10% of expected monthly income.

For purchase questions, the model ends with a clear verdict (yes, tight, or no), the key numbers it relied on, and the reason. 'Yes' means affordable without cutting or delaying anything. 'Tight' means affordable only by cutting or delaying something, and the answer must name what. 'No' means it is not affordable without cutting essentials (such as groceries) or going against the user's stated priorities, and the answer must say which. "Essentials" means groceries, transport needed for work, and anything labeled `fixed_bill`. Everything else is discretionary. There is no allocation block, so the four checks do not apply.

When the numbers do not work (expenses plus events plus goals exceed income), the correct behavior is for the agent to say plainly what it would cut and what that costs me. A tidy allocation that does not balance is a failure.

## Synthetic data

- One generator script with a FIXED SEED so the data is reproducible.
- Output is plain JSON files in a `data/` folder.
- Four test months, each built to force a different path:
  1. **Quiet month:** normal bills, no events, healthy slack.
  2. **Birthday month:** a birthday on the calendar, with last year's birthday spending in the history. You can use October since that's my birthday month.
  3. **Over-budget month:** fixed bills plus an event plus goals exceed income.
  4. **Slow drift:** eating out creeps up about 5% per month and never breaches a limit.
- Also generate a goals file and a priorities file.
- After generating data, tell me what each file contains and which month is meant to test what, so I can read it.
- A scenario.json file in each scenario folder holds the fictional ‘today’ date, and every tool uses that date, never the real system date.
- Each of the four scenarios gets its own folder under data/, and the agent takes the scenario name as an argument when it runs.
- The scenario name only selects which data folder the tools read. Never pass it to the model, and never put scenario labels or hints (like “should cut eating out”) in the data files. The model must discover what matters through the tools.

## Baseline (required)

Write a plain if-statement version in `baseline.py` (fixed bills first, then a simple split such as 50/30/20; a purchase is affordable if it is under what is left). Run it on the same four months. The comparison is how I show where the model earns its place. If the baseline matches the agent on every month, my scenarios are too easy and I need harder ones.

## Verification (I will do this, and you should help)

- Help me READ each file: explain it line by line when I ask.
- Test normal, empty, weird, and boundary cases (a month with no transactions, a negative balance, income exactly equal to expenses).
- Do not write both the code and the only tests for it. I will give the code to a separate chat as a second reviewer.
- Do not hide failures. Show me real traces, including bad runs.

## Repo and security rules

- `.env` holds `ANTHROPIC_API_KEY` and `MODEL_NAME`. It must be in `.gitignore` BEFORE the first commit.
- `.gitignore` includes at least: `.env`, `venv/`, `__pycache__/`, and `logs/scratch/` (throwaway runs). Final run logs in `logs/` ARE committed as evidence.
- Never print, log, or echo the API key. Never write it in any file that is committed, including this one.
- Before every push, run `git ls-files` and confirm `.env` is not listed.
- If a key is ever committed, stop and tell me. Deleting the file does not fix it, because it stays in git history. The key must be rotated.
- Make small, meaningful commits, one per step. Never one big "upload" commit. Use clear messages.
- No real financial data anywhere in the repo.
- Never read, open, or reference any file outside this project folder. If a task seems to need a file elsewhere, ask me first.

## Structure (agreed in step 1)

```
budget-agent/
  CLAUDE.md
  README.md
  .gitignore
  requirements.txt
  .env.example      (placeholder names only, no real key; committed)
  .env              (never committed)
  generate_data.py  (fixed seed; writes all of data/)
  data/
    quiet/          each folder holds: scenario.json (fictional "today"),
    birthday/         balance.json, recurring.json, transactions.json,
    over_budget/      calendar.json, goals.json, priorities.json
    drift/
  tools.py          (fact-only tools; data folder passed in by code)
  prompts.py        (system prompt and tool descriptions)
  agent.py          (the loop; this is the main file)
  checks.py         (the four allocation checks; flag only)
  baseline.py
  run_tests.py      (runs the scenarios and saves the logs)
  logs/             (final logs committed; logs/scratch/ gitignored)
```

## README (required, graded)

Must cover: what the agent does, what problem it solves, how to run it, how to set up `.env` (without the key), that the data is synthetic, which model I used and why, a short note on how I used AI to build it, and what I verified and what I caught.

## Build order (do one step, then stop)

1. Plan and file structure (no code).
2. Data generator, then I read the output.
3. Tools, each tested by hand.
4. The loop.
5. One cheap question end to end, then I read the trace.
6. Baseline.
7. Run all four months and save the logs.
8. README.

## Do not

- Do not use a framework.
- Do not put decisions inside tools.
- Do not pre-load all the data into one prompt. The model must choose what to look up.
- Do not call the API in a loop with no cap.
- Do not use the most expensive model when a cheaper one works.
- Do not commit secrets or real data.
- Do not build more than the current step.