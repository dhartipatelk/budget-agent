# CLAUDE.md: Budget Agent (BUAN 6V99 mini-project)

Read this file fully before doing anything. If anything here conflicts with a request I make in chat, tell me about the conflict before acting.

## What this project is

A budgeting agent, built from scratch in plain Python for a university course. I lose track of what I can afford when events compete for the same money. The agent investigates a (fictional) user's spending history, recurring bills, calendar, goals, and stated priorities, then recommends ONE tradeoff with a reason. It answers two kinds of question with the same loop:

1. "How should I allocate this month's income?"
2. "Can I afford this specific purchase?"

All data is synthetic. Never use, ask for, or generate real bank data. The README must say the data is synthetic.

## Project status (this is a LIVE file)

Due: Monday Oct 12, 2026 at 5:00 PM (firm, no extension). Solo, 20% of the course grade. Graded on: whether it is a real agent (see the hard requirements below), the repo (README, structure, real commit history, no secrets), a five-minute presentation with a live demo, and whether I can explain every file and how I verified it. No UI is required for this assignment.

Done so far:

- Step 1: plan and file structure agreed (Oct 11, 2026). Decisions recorded below.
- Step 2: `generate_data.py` written and run (Oct 11, 2026). Verified: identical output on re-run, no scenario labels in the data, numbers match the plan. Fixed after review: `gas` renamed `transport`, wedding note, goal transfer names, slack and decision #21 corrected to match the data.

- Step 3: `tools.py` written (Oct 11, 2026). I tested every tool by hand in the terminal and checked answers against the JSON files: `get_balance`, `get_recurring_expenses` (totals 3374 / 303.47 / 1277.47), `get_transactions` (found the $260 birthday dinner; Oct 2025 eating out $547.28), `get_category_average` (drift 12-month $290.48 vs 3-month $356.21), `get_goals`, empty cases (no events, empty sum), and 5 bad inputs (wrong capital letter, US date, num_months 0, text instead of number, the forbidden `is_affordable`). All passed; all bad inputs returned an error instead of crashing.
- Step 4: built in four pieces (Oct 12, 2026): 4a `.gitignore` + `.env.example`, 4b `prompts.py`, 4c `checks.py` (tested by hand with fake bad allocations), 4d `agent.py`. `agent.py` was tested OFFLINE with a fake model that follows a script (no API call, no cost): steps run in order, a garbled reply counts as a step, a fake `RESULT:` line after an ACTION is ignored, the scenario name is not in the system prompt (today's date is), a bad allocation is flagged and not fixed, a model that never finishes stops at exactly 25 calls, a purchase answer gives no false alarm, a cut-off reply is flagged. NOT yet tested: real API calls, real response objects, and the real 401/404/429 error paths. Those wait for step 5. Small fixes found while testing: check-header wording, `$-6,300` shown as `-$6,300`, log names to the millisecond.

Steps 5 and most of 7 are DONE; step 6 (baseline) and step 8 (README) are NOT. Where things stand (Oct 12, about 6 AM; I stopped here to sleep):

- What exists: all the code (`generate_data.py`, `tools.py` with 9 tools, `prompts.py`, `checks.py` with 5 checks, `agent.py`, `run_tests.py`), the data, and the traces: `logs/step5_*` and `logs/step7_*` (earlier evidence), `logs/first_set_before_purchase_rule/` (first set of six runs, BEFORE the purchase rule, with `summary.json`) and `logs/final/` (the final set of EIGHT runs, with the purchase rule and the cash-flow definition) and `logs/repeats_purchase_rule/` (questions 5 and 6, three times each, AFTER the rule). Decisions 44 to 52 explain every change and every finding.
- Model: the final runs used `claude-sonnet-5-5` through a command-line override. My local `.env` may still say `claude-haiku-5-5`: fix it (`MODEL_NAME=claude-sonnet-5-5`, check with `grep '^MODEL_NAME=' .env`). `.env.example` already says Sonnet. Haiku 5.5 failed the `over_budget` month (decision 47).
- Git: everything up to `e98c113` is committed and pushed. NOT yet committed after that (check `git status`): the rename of the first set (`logs/final` to `logs/first_set_before_purchase_rule`, already staged), the cash-flow sentence in `prompts.py`, the two new questions in `run_tests.py`, the new final set in `logs/final/`, and this file. Commit in this order: (1) the staged rename; (2) `prompts.py` and `run_tests.py`; (3) `logs/final` and `CLAUDE.md`; then `git ls-files | grep .env` (only `.env.example` may print) and `git push`.
- Findings so far (decisions 44 to 52; for the README): the checks pass on plans that are unrealistic, because they test numbers and completeness, not reasoning; `over_budget` needed a stronger model; `drift` was MISSED ("the summary tool disabled drift detection" is only a hypothesis); the allocation paths barely vary (the same six lookups, 9 to 10 calls) while the conclusions vary; the purchase rule fixed the process (calendar opened 3/3) but made the paths more alike; and "afford" is ambiguous: the allocation uses income only (it says cut shopping) while the purchase answer uses cash flow (it says no cuts needed).

DECISION MADE: "afford" means cash flow (decision 53). The final set of eight runs is done and read (decision 54). Code and prompt are FROZEN again.

Next session starts here (DEADLINE Oct 12, 5 PM; suggested upload by 3 PM): (1) commit as listed above and fix my local `.env` (`MODEL_NAME=claude-sonnet-5-5`, check with `grep '^MODEL_NAME=' .env`); (2) DONE (decision 55): the ladder questions ran as runs 9 and 10 (TIGHT and NO); (3) DONE (decision 56): `baseline.py` written and run; (4) DONE (README written; read it, edit it, check each claim against the logs) (findings in decisions 44 to 54, the baseline comparison, the model choice, and that the allocation uses income only while the purchase answer uses cash flow); (5) real 401 and 404 tests (`ANTHROPIC_API_KEY=bad venv/bin/python3 agent.py quiet "hi"` and `MODEL_NAME=nope venv/bin/python3 agent.py quiet "hi"`; a bad key and a bad model name cost nothing); (6) practise the 5-minute demo twice (the strongest live demo is the `over_budget` allocation). The FEATURE FREEZE (decision 49) stays.

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
22. **Priorities are designed to conflict** (savings vs Roth vs experiences; Solidcore "if I can"). Priorities that never conflict give the model nothing to judge.
23. **The wedding note says "due before the trip"**, not "paid this month." The flight and hotel are not in the transactions or balance, so "paid" would have contradicted the data.
24. **Goal transfer categories renamed** from `savings_transfer` / `roth_ira_contribution` to `savings` / `roth_ira`, matching the goal names, to avoid a naming mismatch later.
25. **Tools do one-right-answer arithmetic** (income still expected, bill totals, amount still due, goal amount remaining, months left), so the model never adds. They never say "on track", "affordable", or "trending up": those are judgments.
26. **`get_category_average` uses FULL months only** (the current month is excluded). Today is the 2nd or 3rd, so a 2-day month would drag the average down and mislead the model. It also returns each month's total so the model can see a trend for itself.
27. **`get_transactions` shows at most 50 rows** (most recent), plus the full count and total, so one call cannot flood the model with ~470 rows (cost and confusion).
28. **Bad input returns `{"error": ...}`, never a crash**, often with the valid options listed, so the model can correct itself and the loop keeps going.
29. **Known limits, for the second reviewer:** (a) a category with no history (for example `gifts` in `quiet`) returns "unknown category", not $0, so that a typo like `Groceries` cannot silently return $0; (b) `run_tool` catches argument errors (TypeError), which helps with model typos but could also hide a bug inside a tool.
30. **The model writes one `THOUGHT:` line before each `ACTION:` or `FINAL:`.** The code still acts only on the ACTION/FINAL line. Why: in the live demo the audience sees WHY each tool was called, not just a list of calls. Costs a few tokens per step.
31. **Stop sequence on `RESULT:`.** The API cuts the model off if it starts writing a fake tool result, so decision #3 is enforced in code, not only in the prompt.
32. **Today's date goes in the system prompt** (from `scenario.json`), so the model can choose date ranges. The scenario NAME is never sent.
33. **No hint about events or history in the prompt** (for example, nothing like "past spending shows what similar events cost"). We want to see whether the model finds last year's birthday on its own. If it does not, add a hint later and say so in the README.
34. **The prompt states the sum rule, the full-fixed-bill rule, and the `unfunded_usd` rule, but NOT the 10% number.** Those rules are the task itself (agreed with the second reviewer). Instead of the number, it says "give spare money a purpose; do not leave it sitting in unassigned", so the quiet month is a real test of where the model puts ~$1,200 of slack. If the 10% check fires, that is an honest finding.
35. **Prompt fix after review: facts vs choices.** The prompt said "Only use numbers that came from a RESULT", which contradicts allocating (the model CHOOSES amounts like "eating_out: 250"; no tool returns them). Now: "Any number you state as a fact must come from a RESULT. The amounts you choose to allocate are your own decision." Caught by the second reviewer.
36. **How `unfunded_usd` is counted in the sum check (my reading of check 3, please confirm).** The sum check adds every allocation line EXCEPT `unfunded_usd`, then subtracts `unfunded_usd` only when it is allowed (fixed bills alone exceed income). Example: income 3000, bills 3200, allocation `{rent 2400, loans 800, unfunded_usd 200}` gives 3200 - 200 = 3000, so it passes. If `unfunded_usd` appears when it is NOT allowed, only check 3 flags it (the sum check ignores the line), so one mistake produces one flag, not two.
37. **Check 2 matches names exactly** (`rent`, not `Rent`), as decided earlier, so a capitalised name is flagged as missing. It is a visible failure, and the fix would go in `prompts.py`. A fixed bill that is HIGHER than its real amount is not flagged by check 2; the sum check catches it if it throws the total off.
38. **Known limits of `checks.py`, for the second reviewer:** (a) a negative amount in the allocation is not flagged, so it could be used to make a sum come out right; (b) when `unfunded_usd` is allowed, the code does not verify it equals the real shortfall; (c) `extract_allocation` reads the LAST ```json block in the answer.
39. **Thinking is left at the model's default for step 5.** Haiku 5.5 thinks by default, and thinking tokens count against `MAX_TOKENS = 2000`, so a long think could cut the visible answer off. The loop prints a WARNING and flags the final answer if the reply is cut off. If that happens in the first trace: raise `MAX_TOKENS` or lower the effort setting, and say so in the README. Haiku 5.5 also rejects sampling settings such as `temperature`, so none are set. (Source: the Claude API reference; confirm on docs.claude.com.)
40. **Assistant replies are added to the conversation exactly as received** (including any thinking blocks), and the code reads text only from the text blocks. Editing earlier turns can invalidate thinking blocks.
41. **A garbled reply counts as a step**, and the model is told what was wrong, so the step cap always applies. API errors, refusals, and step-cap runs are still written to the log (only Ctrl-C loses a log).
42. **Run logs:** one JSON file per run in `logs/scratch/` (gitignored): question, scenario name (metadata only, never sent to the model), each step's reply / tool / arguments / result, final answer, allocation, flags, step count, tokens, how it ended. The file name uses the real clock to the millisecond, for naming only.
43. **Run `agent.py` with the venv Python** (`venv/bin/python3 agent.py ...` or `source venv/bin/activate` first). The system `python3` does not have the `anthropic` package. Cost note: the API reference lists Haiku 5.5 at $0.10 input / $0.50 output per 1M tokens (prompts up to 100K tokens); confirm on the pricing page.
44. **Prompt fix after the first real run (Oct 12, 2026):** the first `quiet` run passed all four checks, but the plan was unrealistic. About $810/month of normal spending had no line (transport $153, shopping $522, entertainment $77, health $57, 6-month averages), eating out was set to the $400 cap instead of the real ~$267, savings absorbed the gap ($2,692.53 vs planned $1,667), "experiences $800" was invented, and the answer said savings would reach $12,695 "by year-end" (that is only the balance after this month's transfer). The four checks cannot see missing categories, which is a limit of the checks, not a bug. Cause: the model looked up only groceries, and the prompt never said the allocation must cover everything the person spends on. Fix: one general rule in the allocation block ("Cover the whole month: also include a line for every category the person regularly spends in... get_category_average shows what a category typically costs."). It applies to every scenario and hints at no answer. The "before" trace is saved as `logs/step5_quiet_before_prompt_fix.json`. NOT fixed by this rule: the misleading "by year-end" claim and the model doing some arithmetic in its head; watch for both in later traces.
45. **9th tool `get_spending_summary(num_months)` added** (my decision). Facts only: for every category with transaction history it returns the average monthly spend over the last N FULL months (this month excluded), alphabetical, with months that have no spending counted as $0. It includes bills, subscriptions and goal transfers (`rent`, `savings`, `roth_ira`) as well as everyday spending, so the model must sort out which is which and avoid double counting; that is judgment, not the tool's job. Same `num_months` rule and error message as `get_category_average`. To make that identical by construction, the two shared pieces were moved into helpers (`_parse_num_months`, `_last_full_months`) and `get_category_average` now uses them; I checked it returns identical results on 979 cases before and after. In `prompts.py` I added the tool's description and ALSO changed one phrase in the "Cover the whole month" rule so it points at the new tool ("get_spending_summary lists every category and what it typically costs") instead of `get_category_average`; revert that phrase if it reads as too much of a hint.
46. **Same-month-last-year fact added to `get_spending_summary`** (my decision, after the `over_budget` runs). Both Haiku 5.5 and Sonnet 5.5 asked for a 6-month window (June to November), so last December's gifts ($400) fell outside it and the model saw gifts = $0. Sonnet then wrote "You normally spend nothing here", which was false. My first reaction was to file this as a README limitation; I was asked why I did not try to fix it first, and the fix is small. Each category now also returns `same_month_last_year_usd` (the full calendar month one year before today; null if the history does not reach back that far), and the response has `same_month_last_year` (for example "2025-12"). Facts only: no "seasonal" label. I chose a tool field over a prompt rule ("check last year") because a rule would make every run do the same lookup, so paths would stop varying (hard requirement 2). The model can still ignore the field; the re-run of `over_budget` shows whether it does. Checked: the averages in the summary agree with `get_category_average` in 339 of 340 comparisons; the one difference is a half-cent tie (drift, transport, 6 months: exact average $166.615, shown as 166.62 by the summary and 166.61 by `get_category_average`, because they add the numbers in a different order). Not a logic bug.
47. **Model: Haiku 5.5 failed the `over_budget` test; Sonnet 5.5 passed the wedding part.** Same question, same prompt. Haiku never opened the calendar, missed the $1,350 wedding, said "no shortfall" and added $700 to entertainment, and the checks still passed (`logs/step7_over_budget_haiku_first_run.json`). Sonnet 5.5 found the wedding, made it its own line, saw it was $104.70 over, cut shopping from $447 to $193, and kept savings, Roth, Solidcore and groceries (about $0.085 vs $0.005 per run; saved as `logs/step7_over_budget_sonnet_run.json` if committed). My project rule says to move to a stronger model only if the cheap one's judgment on the over-budget month is clearly weak; it was. Plan: use `claude-sonnet-5-5` for all final runs (one model keeps the comparison clean), keep the Haiku traces as evidence. Done by setting `MODEL_NAME` in `.env`, no code change.
48. **Two changes proposed by the second reviewer after the Sonnet re-run (Oct 12, 2026).** (a) A disclosure rule in the prompt: "If you set any category below what it typically costs, say which one and by how much." Why: the model trimmed eating out from $282 to $250 without saying so. It is about disclosure, not about what the answer should be, so it does not narrow the paths. (b) Check 5 in `checks.py` (see the list above). It is the first check about completeness rather than arithmetic, and it came from a failure found by running the agent. I tested the rule on SAVED allocations before building it: it flags `gifts` ($150 vs $400) on the latest Sonnet run (wanted) and on the Haiku run ($0 vs $400); it also flags `shopping` on the Sonnet run ($225.13 vs $510.63), which is the agent's deliberate, disclosed cut (the reviewer had predicted gifts only); on `quiet` run 3 it flags nothing; on `quiet` run 1 it flags `shopping` and `transport` as missing (correct). So it will sometimes flag a justified answer, and the README must say so instead of calling the check clean. Also corrected: the reviewer said capping October eating out at $400 would fire it on the `birthday` month; it would not ($400 is more than half of $547.28); it fires at about $273 or less. The thresholds live in `checks.py` and here, not in the prompt, like the 10% in check 4. After this change the prompt, tools and checks are FROZEN: any later change makes the final runs stale.
49. **Feature freeze, and why check 5 stays as it is (Oct 12, 2026).** In the re-run with the disclosure rule and check 5 (`logs/step7_over_budget_sonnet_with_check5.json`), the model named its shopping cut ("$304.70 below its usual $447.21", the figure computed with `sum_amounts`), and check 5 fired on `shopping` (a justified, disclosed cut) but NOT on `gifts`: the model set gifts to $200, exactly half of last December's $400, and the rule says "below half". I recommended changing `<` to `<=`. The second reviewer argued against it and I agree: 50%, 60% and "half or less" are all arbitrary, so moving one because a single run sat on its boundary is overfitting (a $210 gifts line would be missed again). Fixes of the earlier kind were principled (the model lacked a FACT, so we gave it one; it did not SAY what it cut, so we asked it to). Here there is no principled value. Decision: leave check 5 as it is and document the miss. The only change I would consider later is dropping the ratio and flagging on dollars alone (last year exceeds the allocation by at least about $150): one arbitrary number instead of two and no boundary to sit on; on this run it would flag gifts and shopping, and it avoids the birthday false positive ($547 last October vs a $400 cap is a $147 gap). Not built. README NOTES: (a) the $400 never reached the person: it appears in the model's step-4 thought and nowhere in the final answer, and the disclosure rule did not cover it because gifts' 6-month average is $0, so $200 is above "typical" and nothing triggered; a real gap in how the rule is worded; (b) the disclosure rule pushed `over_budget` from 10 steps to 13 and from about $0.10 to $0.14, because the model now does every subtraction with `sum_amounts` (good for the no-mental-arithmetic rule, it costs steps); (c) check 5 can flag a justified cut, so a flag is for a human to read, not a verdict; (d) the story to tell: "the model set gifts to exactly half, my threshold said below half, so it missed the case I built it for, and I left the number alone rather than tuning it to the run that exposed it."
50. **First set of six final runs (Oct 12, 2026, Sonnet 5.5 through a command-line `MODEL_NAME` override because `.env` still said Haiku; the logs record the model; saved in `logs/first_set_before_purchase_rule/` (moved there on Oct 12) with `summary.json`; about $0.59 in total: 238,862 tokens in, 11,262 out).** No errors, no cap hits, no crashes. Results: (1) `quiet` allocation, 10 steps, good: all categories covered, the $1,151 spare went to savings (+$901), eating out (+$100) and entertainment (+$150), it noted the $1,667 plan already keeps the savings goal on pace so the extra is a cushion; checks passed. (2) `birthday`, 11 steps, good: it saw the birthday, raised eating out to $400 and entertainment to $130, but never cited last October's $547; checks passed. (3) `over_budget` allocation, 11 steps, good: found the $1,350 wedding, cut shopping $447 to $192.51 and said so ("$254.70 below its typical"), set gifts to $150, citing last year's $400 and calling the $150 "a guess"; check 5 flagged `gifts` and `shopping`. (4) `drift`, 11 steps, MISSED: it gave eating out $390 ("$56.48 above typical") and never mentioned that eating out has climbed every month (July was $377.54, the 6-month average is $333.52). (5) `quiet` purchase ($400 weekend trip), 9 steps, good: YES, $1,150.73 of slack. (6) `over_budget` purchase ($300 night out), 6 steps, WRONG: it said YES "without cutting or delaying anything" but never opened the calendar, goals or priorities, so it ignored the $1,350 wedding; the real cushion is $941.30 - $1,350 = about -$409 (before gifts), so the right verdict is TIGHT at best (CORRECTED in decision 52: that used income only and ignored the checking balance). No check covers purchase answers, so nothing caught it. FINDINGS FOR THE README: (a) a confidently wrong purchase verdict (run 6), and it was the SHORTEST run, so fewer tool calls was worse, not better; (b) the drift trend was missed, and no run called `get_category_average` (the tool with the monthly totals) or `get_transactions`, because `get_spending_summary` made them unnecessary, so adding the summary tool fixed completeness but removed the model's route to the drift signal; (c) WEAK PATH VARIATION: the four allocation runs used 9, 10, 10 and 10 tool calls and the same six lookup tools (balance, recurring, summary, goals, priorities, calendar) in a slightly different order; what varied was the conclusion, not the path; the purchase runs varied more (8 vs 5 calls); this does not meet hard requirement 2 ("a quiet month should take few tool calls and a crunch month many") strongly, and the README must say so; (d) all of this is from ONE run per question, so it is a sample, not a measurement. DECISION MADE: the purchase rule was added (decision 51).
51. **Purchase rule added (Oct 12, 2026).** The allocation path got "Cover the whole month" after the first `quiet` run failed; the purchase path never got an equivalent, so nothing told the model that a verdict on spending money needs what is already committed or coming. One sentence in the purchase section: "To judge a purchase, first find out what else is committed or coming this month, not only what is already paid." It is deliberately softer than "check the calendar", so the model still chooses its tools. One wording, and whatever comes out is reported, including if run 6 still says YES (the next escalation under my model rule would be a stronger model, with the evidence). HONEST TRADEOFF with hard requirement 2: the rule should make the purchase paths MORE alike (run 6 took 6 steps, the quiet purchase 9; both should now look at commitments), so it narrows variation; correctness is worth it, and I must not claim the rule helps variation. The evidence for "the next step depends on what the last step found" is in the THOUGHT lines (for example `over_budget` run 3, step 4: "Gifts were $400 last December, so I should check the calendar for December plans"), not in tool counts, and the 6 steps of run 6 must not be counted as variation because that run was wrong. To vary the PATH honestly, vary the QUESTIONS (for example a $25 lunch vs a $2,500 laptop on `quiet`), not the agent. DRIFT NOTE FOR THE README: after the summary tool was added, no run called `get_category_average` (the tool with monthly totals) and the drift was missed, but `drift` was never run before the summary tool existed, so "the tool disabled detection" is a HYPOTHESIS, and the model did have a signal (6-month eating-out average $333.52 vs $216.26 for the same month last year) and did not mention it; I am not fixing it, because the only fix would be a rule telling it to look for trends, which is a hint. `.env.example` now says `claude-sonnet-5-5` (someone who clones the repo copies `.env.example`, not `.env`). Repeat test: questions 5 and 6 three times each, logs in `logs/repeats_purchase_rule/`; the first set of six (before this rule) is in `logs/final/`.
52. **Result of the purchase-rule repeat test, and a CORRECTION to decision 50 (Oct 12, 2026).** Six runs (questions 5 and 6, three times each; logs in `logs/repeats_purchase_rule/`; Sonnet 5.5; one BAD_REPLY recovered). PROCESS: the calendar was opened in 3/3 `over_budget` purchase runs (before the rule: 0 of 1) and the $1,350 wedding was counted in all three; the purchase paths became MORE alike (steps: `quiet` 9, 11, 9; `over_budget` 9, 8, 8; before: 9 vs 6), as predicted in decision 51 (the reviewer had predicted the opposite). One genuinely adaptive step: `quiet` run 2 called `get_transactions` to see what was already spent this month. VERDICTS: YES in all six. CORRECTION: decision 50 said the right `over_budget` verdict was "TIGHT at best (about -$409)". That used INCOME ONLY. The model used CASH FLOW (checking $3,930.24 + $4,350 still to come - everything still owed, wedding included), which leaves about $1.5k to $2.4k, and the checking balance includes a $2,100 carry-over from before the month (`CHECKING_BUFFER_USD` in the generator). So "wrong" depended on a framing I had not disclosed; I overstated it, and the reviewer's "worst output in the set" claim was built on my number. REAL FINDING: in the same month the ALLOCATION answer (income only, by design: the block must sum to expected income) says "cut shopping $255 to pay for the wedding", while the PURCHASE answer (cash) says "no cuts needed"; two framings of "afford" disagree. A second, separate problem: `over_budget` purchase run 2 said the night out would put eating out at about $582 against the stated $400 target and advised keeping other eating out light, which is TIGHT by my own definition, yet it said "YES, without cutting or delaying anything"; it also left shopping (about $447) out of its total, so its leftover ($2,022.75) was overstated (the same arithmetic with shopping gives $1,575.54, which run 3 got). DECISION PENDING: what "afford" means. Recommendation: cash flow (the balance is in the data and the model's method is sound), documented in the README together with the difference from the allocation framing; no more prompt rules. If "income only" is chosen, a rule and a full re-run are needed.
53. **DECISION: "afford" means CASH FLOW (Oct 12, 2026).** I chose cash. Why: the checking balance is in the data and a person judging a purchase looks at cash, and the repeat test (decision 52) showed the model switching between two accountings from run to run (quiet purchase: $750.73 leftover when it used income only, $2,850.73 when it used cash), so the prompt now pins it down. One sentence added to the purchase section of `prompts.py`: "Judge affordability against this month's cash: the checking balance plus income still to come, minus bills still due, planned goal transfers, and typical spending still to come." It is a definition, not a hint about any answer, and it reopens the freeze (decision 49) by exactly one sentence. The allocation answer still uses income only, by design (the block must sum to expected income), so the README must say the two answers frame "afford" differently. Not fixed by it, on purpose: a verdict that contradicts the definitions already in the prompt (decision 52, run 6b said YES while its own text put eating out at $582 against the $400 target, which is TIGHT or NO by the definitions we gave it); that is the model misapplying a definition, not a hole in the wording, so I am NOT narrowing the YES wording. The old logs are kept: `logs/first_set_before_purchase_rule/` (six runs, before the purchase rule), `logs/repeats_purchase_rule/` (questions 5 and 6 three times each, with the look-up-commitments sentence), and the new final set in `logs/final/` (EIGHT runs: the six plus a $25 lunch and a $2,500 laptop on `quiet`). Cost note: about $0.80 for the eight.
54. **Final set of eight runs (Oct 12, 2026, about 10:30 AM; Sonnet 5.5; `logs/final/`; about $0.71: 286,741 tokens in, 13,747 out; no errors, no cap hits, no bad replies).** With the cash-flow definition in the prompt (decision 53): (1) all four purchase runs now use the SAME accounting (cash: balance + income still to come - bills still due - goal transfers - typical spending); leftovers: $2,850.73 ($400 trip, quiet), $1,571.54 ($300 night out, over_budget, wedding counted), $3,250.73 ($25 lunch), $750.73 ($2,500 laptop). (2) THE PATH VARIES WITH THE QUESTION, not with the month: the $25 lunch took 6 steps and 4 lookups (no calendar, no priorities); the $2,500 laptop took 8 steps, the $400 trip and the $300 night out 9 steps, with all six lookups; the four allocation runs (the four months) all used the same six lookups (9, 10, 10 and 10 steps). (3) NO TIGHT OR NO HAS EVER APPEARED: all purchase runs so far (three sets) said YES, so the verdict ladder (yes, tight, no) has never been exercised, and a rule-based baseline would also say YES to all of them. (4) ALLOCATION: `quiet` and `birthday` look good; `birthday` gave eating out $375 against $547 last October without citing last year (check 5 does not fire because $375 is more than half), so the birthday sizing is only partly tied to history; `drift` was MISSED again (eating out set to $400, "right at your limit", no mention of the monthly climb); `over_budget` found the wedding, cut shopping from $447 to $193 and named it, but this time did NOT call the $150 gifts line a guess or cite last year's $400 (earlier runs did), so uncertainty labelling varies from run to run; check 5 flagged `gifts` and `shopping`. (5) `over_budget` purchase still says "YES, without cutting or delaying anything" while its own caveat says the night out could push eating out to $582 against the $400 guideline if it is on top of usual eating out (it conditions on how the $300 is categorised): better than before, still partly inconsistent with the TIGHT definition. (6) FOR THE README: the agent applies the definitions it is given unevenly, and one run per question is a sample, not a measurement.
55. **The verdict ladder was exercised (Oct 12, 2026, about 1:30 PM; Sonnet 5.5; runs 9 and 10 in `logs/final/`; about $0.19).** Both are `over_budget` purchase questions with the cash-flow definition. RUN 9, "$2,500 laptop this month": **TIGHT**. Cash left after bills, goal transfers, the $1,350 wedding and typical spending was $1,871.54, so the laptop leaves -$628.46; it said to cut all of shopping ($447.21) plus $181.25 from eating out and entertainment, protected savings, Roth, groceries and Solidcore, named the unknowns (Holidays at Mom's, last December's $400 gifts) and suggested waiting until January. I added its arithmetic by hand and it is right. The SAME item on `quiet` (run 8) gave **YES** with $750.73 left: same purchase, different month, different verdict. RUN 10, "$6,000 international vacation this month": **NO**: $1,932.53 short before any discretionary spending, and still $832.60 short after cutting every discretionary category including Solidcore; it said the only way to cover it would be to take from savings or the Roth, which are priorities. CAVEATS: run 10 never opened the calendar, so its shortfall leaves out the $1,350 wedding (the real shortfall is $1,350 larger; the verdict is unaffected but the "find out what else is coming" sentence was ignored in that run); run 10 also had one BAD_REPLY, recovered at the next step. Expected outcomes were NOT pre-labelled; the arithmetic decides what is defensible (cash left -$628 needs cuts the model can name, so TIGHT; -$4,128 is more than all discretionary spending plus both goals, so NO). All three verdicts (YES, TIGHT, NO) have now appeared. `logs/final/summary.json` still covers only runs 1 to 8, because a partial run never overwrites it; a full run of all ten would refresh it (about $0.9).
56. **Baseline run and comparison (Oct 12, 2026; `baseline.py`, output in `logs/baseline_comparison.txt`).** ALLOCATION: the baseline differs from the agent on all four months, but only some differences are clear. (a) `over_budget`: the baseline cannot see the calendar, so its plan has no $1,350 wedding line (the plan is tidy but unrealistic by $1,350), gives gifts $0 (check 5 flags it), puts $3,533 into savings against a goal that needs only $1,663, and keeps shopping at $447; the agent budgets the wedding, funds exactly the $1,663 the goal still needs, and cuts shopping $255. (b) In all four months the baseline has no `roth_ira` line (its money sits in the single savings line), so check 5 flags "roth_ira is missing" four times: it drops a separately stated priority (the check works on names, so this is partly an artefact of how the baseline labels things). (c) `quiet` and `birthday`: the agent shifts about $100 to eating out and $120 to $200 to entertainment and keeps the Roth, the baseline puts all spare money into savings; these are judgment calls that follow the stated priorities, not clear wins; the baseline is not wrong. (d) `drift`: both MISS the trend, and the baseline is arguably more conservative ($333.52 for eating out against the agent's $400, which sits at the limit). PURCHASES (6 questions with saved agent runs): baseline and agent agree on 4 (YES, YES, YES, NO for $300, $25, $400 and the $6,000 vacation); they differ on both $2,500 laptops: `over_budget` baseline NO vs agent TIGHT (with a concrete way to afford it: cut all shopping plus $181 from eating out and entertainment; the baseline can only say NO), and `quiet` baseline NO vs agent YES (a FRAMING difference: the baseline compares the price with what is left of this month's income, the agent counts cash on hand including the $2,100 carried over; do not claim the agent is smarter here, say which definition each uses). HONEST READING: the model earns its place where it needs the calendar, the goal targets and the stated priorities (the over_budget allocation, the TIGHT answer with named cuts, the Roth line); where only averages matter (drift, `quiet` and `birthday` allocation, most purchase verdicts) a rule does about as well. The baseline does not match the agent in every month, so the scenarios are not trivially easy. One run per question, so these are samples.
57. **No rubric or evaluation sheet in the repo (Oct 12, 2026).** A second reviewer suggested scoring the runs on five criteria (priority alignment, context awareness, historical reasoning, transparency, uncertainty). I built a sheet generator and recommended it, and I wrongly called it "required". My professor did not require it and my project file never mentions one; the graded items are the real agent, the repo (README, structure, commit history, no secrets), the five-minute demo, and explaining every file and how I verified it, plus the required baseline and README. I decided I do not want it in the repo, so `rubric_sheet.py` and `evaluation_rubric.md` were removed with `git rm` (they remain in the git history of one earlier commit; they contain no secrets). The README's "what I verified and what I caught" is built from the traces, the baseline comparison and decisions 44 to 56 instead.

Open questions: (anything I still need to ask my professor)

- (none right now. The deadline is firm: Oct 12, 5:00 PM.)

### End-of-session rule

When I say I am finished for the day, update this file before we stop: move finished items to "Done so far", note what comes next, record any design decisions and any problems found, and keep the file index below accurate. Never put the API key or any real data in this file. When I start a new session, read this file first and tell me where we left off.

### File index

Keep this list current so a fresh session knows what each file is for. (Fill in as files are created.)

- `CLAUDE.md`: project instructions and live status (this file).
- `README.md`: the graded README (written Oct 12, 2026; first person, for the professor): what the agent does, the problem, synthetic data, how it works, how to run it, `.env` setup, model choice (Haiku then Sonnet 5.5, with the evidence), one trace from tool result to decision to check, the ten final runs, the baseline comparison, what I verified, what I caught, known limits, how I used AI, and the seven requirements checked honestly. Every path in it was checked to exist and its numbers were spot-checked against the logs; I must still read it and be able to explain every claim.
- `.gitignore`: keeps `.env`, `venv/`, `__pycache__/`, `logs/scratch/` out of git.
- `.env.example`: template with the two setting names and a FAKE key. Copy it to `.env` and fill in the real key there.
- `prompts.py`: the system prompt (reply format, the 8 tool descriptions with when each is useful, the answer formats). `build_system_prompt(today)` fills in the date.
- `checks.py`: the five allocation checks (sum, fixed bills, unfunded, unassigned, below-last-year). Flags only; never fixes. Also `extract_allocation(text)` (pulls the ```json block out of the final answer) and `check_scenario(data_dir, allocation)` (loads the real income and fixed bills, then runs the checks).
- `agent.py`: the loop (main file). `python3 agent.py <scenario> "<question>"` (use the venv Python). `run_agent(...)` is a generator that yields each step; `show(...)` prints them; one JSON log per run in `logs/scratch/`. Constants at the top: `MAX_STEPS = 25`, `MAX_TOKENS = 2000`, `MAX_RETRIES = 3`.
- `run_tests.py`: runs the TEN final questions (allocation on `quiet`, `birthday`, `over_budget`, `drift`; a purchase question on `quiet` and on `over_budget`; plus a small ($25 lunch) and a large ($2,500 laptop) purchase question on `quiet`, to show that the path varies with the QUESTION; and a $2,500 laptop and a $6,000 vacation on `over_budget`, the verdict ladder), prints every step, and saves one log per run in `logs/final/` (committed, not ignored) plus `logs/final/summary.json` with the tool sequence per run (the evidence that the path varies). `venv/bin/python3 run_tests.py` runs all eight; `venv/bin/python3 run_tests.py 3 5` runs only runs 3 and 5 (a partial set never overwrites the summary). One crashed run does not stop the others. Tested offline with a fake model, then used for the final runs.
- `baseline.py`: the plain if-statement version (no model, no API): bills and subscriptions in full, every everyday category at its 6-month average, all that is left to savings; a purchase is YES if its price is no more than what is left after bills, everyday averages and a 20% savings share of income, else NO. Runs the same five checks and prints its allocation next to the agent's newest saved allocation in `logs/final/`, and its purchase verdicts next to the agent's; saves `logs/baseline_comparison.txt`. Run `python3 baseline.py` (works with the system Python).
- `requirements.txt`: Python packages (`anthropic`, `python-dotenv`, and their dependencies). No frameworks.
- `generate_data.py`: builds the synthetic data (fixed seed 42). Run `python3 generate_data.py`.
- `data/<scenario>/`: generated JSON for `quiet`, `birthday`, `over_budget`, `drift` (7 files each). Do not edit by hand; change the generator and re-run.
- `tools.py`: the 9 fact-only tools plus `run_tool(data_dir, name, args)`, which looks a tool up by name and never crashes. Hand-test example: `python3 -c "from tools import run_tool as t; print(t('data/quiet', 'get_balance', {}))"`.

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
- `get_spending_summary(num_months)`: average monthly spend for EVERY category with history (bills, subscriptions, goal transfers and everyday spending) over the last N full months, alphabetical, no judgment, plus what each category cost in the same calendar month one year ago (`same_month_last_year_usd`). Added after the first real runs showed the model could not discover categories (decisions 44 and 45).
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
5. **Below-last-year check:** for each category that has a same-month-last-year value (fixed bills excluded, they belong to check 2), flag it if the allocation is below 50% of that value AND the gap is at least $100 (`LAST_YEAR_FRACTION = 0.5`, `LAST_YEAR_GAP_USD = 100` in `checks.py`; both numbers are arbitrary). A category missing from the allocation counts as $0. It can flag a justified cut, so a flag is something for a human to read, not a verdict.

For purchase questions, the model ends with a clear verdict (yes, tight, or no), the key numbers it relied on, and the reason. 'Yes' means affordable without cutting or delaying anything. 'Tight' means affordable only by cutting or delaying something, and the answer must name what. 'No' means it is not affordable without cutting essentials (such as groceries) or going against the user's stated priorities, and the answer must say which. "Essentials" means groceries, transport needed for work, and anything labeled `fixed_bill`. Everything else is discretionary. There is no allocation block, so the checks do not apply.

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