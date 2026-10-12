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
- Step 2: `generate_data.py` written and run (Oct 11, 2026). Verified: identical output on re-run, no scenario labels in the data, numbers match the plan. Fixed after review: `gas` renamed `transport`, wedding note, goal transfer names, slack and decision #21 corrected to match the data.

- Step 3: `tools.py` written (Oct 11, 2026). I tested every tool by hand in the terminal and checked answers against the JSON files: `get_balance`, `get_recurring_expenses` (totals 3374 / 303.47 / 1277.47), `get_transactions` (found the $260 birthday dinner; Oct 2025 eating out $547.28), `get_category_average` (drift 12-month $290.48 vs 3-month $356.21), `get_goals`, empty cases (no events, empty sum), and 5 bad inputs (wrong capital letter, US date, num_months 0, text instead of number, the forbidden `is_affordable`). All passed; all bad inputs returned an error instead of crashing.

Not done yet: build steps 4 to 8.

Next session starts here: step 4, the loop (`agent.py`, `prompts.py`). Give the plan first. Verify the model name on docs.claude.com before putting it in `.env`.

### Step 2 plan (built; numbers below match the generated data)

- Fixed seed (42). Never uses the real date. All numbers below are made up (confirmed Oct 11, 2026).
- One fictional person ("Maya") in all four scenarios; each scenario is a different "today" with 12 months of history before it. Each folder is self-contained with all 7 files.
- Income: $8,700/month take-home, paid $4,350 on the 1st and $4,350 on the 15th.
- Fixed bills (`fixed_bill`): rent $2,400, student loans $350, car insurance $180, utilities $120, phone $70, internet $70, renters insurance $15, orthodontic payment $169 (final payment 2027-02-10, so 3 left in December). Total $3,374.
- Subscriptions (`subscription`): Solidcore $258, AppleCare $20, streaming $15.49, Spotify $6.99, iCloud $2.99. Total about $303.
- Typical flexible spend (random noise): groceries ~$500, eating out ~$270, shopping $200 to $600 (supplements, hygiene, clothes, makeup, skincare), transport (gas) ~$160, entertainment ~$80, health/copays ~$50. Total about $1,410.
- Goal transfers are logged in transactions under the SAME names as the goals (`savings`, `roth_ira`), so there is no naming mismatch.
- Goals (NOT fixed bills, so the agent may trade them off): save $20,000 in 2026 ($1,667/month), Roth IRA $625/month ($7,500 for the year), brokerage investing (no target).
- Monthly slack before brokerage, measured from the generated data (income minus everything spent, full months): about $1,200 on average, about $1,000 to $1,470 in normal months. Lower in last October (birthday) and last December (gifts).
- Priorities (Maya's own words, not a ranking): "Saving $20,000 this year is my main money goal." "Contributing to my Roth IRA every month is a priority." "Other investing, like stocks or crypto, matters less to me than experiences and memories with friends." "Eating clean matters to me. I don't want to cut back on grocery quality." "Solidcore is important for my health, and I'd keep it if I can." "I try to keep eating out under $400 a month."

| Folder | Today | What is different | What it should force |
|---|---|---|---|
| `quiet/` | 2026-07-02 | Nothing; about $1,200 slack | Few tool calls; decide where the extra goes |
| `birthday/` | 2026-10-03 | Calendar: "My birthday" Oct 18 (no cost listed). Last October's history has a $260 dinner and $180 shopping | Model looks back at last year and sets money aside |
| `over_budget/` | 2026-12-02 | Friend's wedding in Denver Dec 18 to 20 (flight $520 + hotel $830 = $1,350 listed on the event, "due before the trip", not yet paid) plus holiday gifts (~$400 last December) and a past wedding gift ($200, May 2026). About $150 to $250 over from the wedding alone; about $750 to $850 over once last year's gifts are counted | Model must cut and name the cost; Roth and savings both protected by priorities, so there is no obvious answer |
| `drift/` | 2026-08-03 | Eating out rises 5%/month, ~$220 to ~$375; never passes the stated $400 | Model notices the trend by comparing averages |

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
13. **Recurring items have a `kind` field: `fixed_bill` or `subscription`.** Only `fixed_bill` items (rent, loans, insurance, etc.) must appear at their full amount. Cancelling a subscription is a legitimate tradeoff, so it is not flagged.
14. **Purchase verdicts are yes / tight / no**, with "essentials" defined (see "The final answer and the math check"). "No" depends on essentials and stated priorities, not arithmetic alone, so it stays a real judgment that an if-statement could not make.
15. **A $400 eating-out limit is in the priorities** (raised from $350 when the budget changed). The drift scenario "never breaches a limit," so a limit must exist for drift to mean anything.
16. **A `transport` category exists in transactions** (gas purchases), named to match the "transport needed for work" essential, so the model does not have to guess whether gas counts. (Was `gas`; renamed after review.)
17. **The wedding event lists its known costs; the birthday does not.** Booked prices are facts. For the birthday, the model has to dig through last year's history, so the two paths differ.
18. **Budget redesigned (Oct 11, 2026):** income $8,700, car payment removed, groceries $500, eating out $270. Numbers are made up, not the student's real finances.
19. **Roth IRA and savings are goals, not fixed bills.** A fixed bill can never be reduced (check 2). The priorities protect them instead, so the agent can still weigh them in a true crunch, and a trace shows whether it respected Maya's priorities.
20. **The orthodontic payment has a final payment date** (2027-02-10). The data states only the fact; a good agent may reason "this frees $169 soon." An if-statement would not.
21. **Wedding costs set to $1,350, and December is kept as is.** Measured from the data: the wedding alone puts December only about $150 to $250 over; it becomes about $750 to $850 over once the model finds last December's holiday gifts (~$400) and the past wedding gift ($200). Kept deliberately: the deeper crunch only appears if the agent reads history, which is the judgment the baseline cannot make. (An earlier version of this note wrongly said "over even before gifts"; corrected after review.)
23. **The wedding note says "due before the trip"**, not "paid this month." The flight and hotel are not in the transactions or balance, so "paid" would have contradicted the data.
24. **Goal transfer categories renamed** from `savings_transfer` / `roth_ira_contribution` to `savings` / `roth_ira`, matching the goal names, to avoid a naming mismatch later.
22. **Priorities are designed to conflict** (savings vs Roth vs experiences; Solidcore "if I can"). Priorities that never conflict give the model nothing to judge.
25. **Tools do one-right-answer arithmetic** (income still expected, bill totals, amount still due, goal amount remaining, months left), so the model never adds. They never say "on track", "affordable", or "trending up": those are judgments.
26. **`get_category_average` uses FULL months only** (the current month is excluded). Today is the 2nd or 3rd, so a 2-day month would drag the average down and mislead the model. It also returns each month's total so the model can see a trend for itself.
27. **`get_transactions` shows at most 50 rows** (most recent), plus the full count and total, so one call cannot flood the model with ~470 rows (cost and confusion).
28. **Bad input returns `{"error": ...}`, never a crash**, often with the valid options listed, so the model can correct itself and the loop keeps going.
29. **Known limits, for the second reviewer:** (a) a category with no history (for example `gifts` in `quiet`) returns "unknown category", not $0, so that a typo like `Groceries` cannot silently return $0; (b) `run_tool` catches argument errors (TypeError), which helps with model typos but could also hide a bug inside a tool.

Open questions: (anything I still need to ask my professor)

### End-of-session rule

When I say I am finished for the day, update this file before we stop: move finished items to "Done so far", note what comes next, record any design decisions and any problems found, and keep the file index below accurate. Never put the API key or any real data in this file. When I start a new session, read this file first and tell me where we left off.

### File index

Keep this list current so a fresh session knows what each file is for. (Fill in as files are created.)

- `CLAUDE.md`: project instructions and live status (this file).
- `.gitignore`: keeps `.env`, `venv/`, `__pycache__/` out of git.
- `requirements.txt`: Python packages (`anthropic`, `python-dotenv`, and their dependencies). No frameworks.
- `generate_data.py`: builds the synthetic data (fixed seed 42). Run `python3 generate_data.py`.
- `data/<scenario>/`: generated JSON for `quiet`, `birthday`, `over_budget`, `drift` (7 files each). Do not edit by hand; change the generator and re-run.
- `tools.py`: the 8 fact-only tools plus `run_tool(data_dir, name, args)`, which looks a tool up by name and never crashes. Hand-test example: `python3 -c "from tools import run_tool as t; print(t('data/quiet', 'get_balance', {}))"`.

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
- **Tell me every time it is time to commit and push**, with the exact commands. Commit when one small piece works and I have read it (a file, a fix, a CLAUDE.md update). Review fixes get their OWN commit, separate from the thing they fix, so the history shows "built, reviewed, fixed." Push right after every commit, after checking `git ls-files` shows no `.env`. (My professor wants small, steady commits, not everything at once.)
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