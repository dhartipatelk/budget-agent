# Budget Agent

A budgeting agent built from scratch in plain Python for **BUAN 6V99 (Agentic AI & Process Automation)**.
Author: Dharti Patel. Due Monday, October 12, 2026.

**The problem:** when a wedding, a birthday or the holidays compete with rent and savings, I lose track of what I can afford. This agent looks up a (fictional) person's bills, spending history, calendar, goals and stated priorities, then recommends one tradeoff and says why.

## What it does

The agent helps one (fictional) person decide how to use her money when events compete for it. It answers two kinds of question with the same loop:

1. **"How should I allocate this month's income?"** It ends with one recommended tradeoff, a reason, and an allocation of the whole month's income as JSON.
2. **"Can I afford this specific purchase?"** It ends with a verdict, **YES**, **TIGHT** or **NO**, the numbers it relied on, and the reason.

It does not get the data handed to it. It starts with only a question and decides, one step at a time, what to look up: balance, bills, spending history, calendar, goals, stated priorities. Then it decides what to recommend. (All data is synthetic; see below.)

## How to run it

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then put your own key in .env (see below)
python3 generate_data.py        # optional: data/ is already in the repo
python3 agent.py over_budget "How should I allocate this month's income?"
python3 agent.py quiet "Can I afford a $400 weekend trip with friends this month?"
python3 run_tests.py            # the ten final questions, about $0.90 on Sonnet 5.5
python3 baseline.py             # the rule-based version, no API calls
```

Scenario names: `quiet`, `birthday`, `over_budget`, `drift`. I used Python 3.9 and `anthropic==0.125.0` with `python-dotenv` (no framework).

### Setting up `.env`

`.env` holds two settings and is **git-ignored. Never commit it.** Copy `.env.example` and fill in your own values:

```
ANTHROPIC_API_KEY=your-key-here
MODEL_NAME=claude-sonnet-5-5
```

The model name comes from `.env`, not from the code, so a model can be swapped without editing any file.

## The problem it solves

I lose track of what I can afford when a birthday, a trip or a wedding competes with rent, savings and everyday spending. A fixed rule (like 50/30/20) can't see a wedding on the calendar or know that someone cares more about her Roth IRA than about brokerage investing. The point of this project is to find out **where a model's judgment adds something a fixed rule cannot**, and to test honestly where it does not.

## The data is synthetic

**All data is made up.** There is no real bank data anywhere in this repo. `generate_data.py` builds one fictional person, "Maya" ($8,700 monthly take-home, rent, loans, subscriptions, goals), with a fixed random seed (42), so the data is identical every time. It writes four test months, one folder each, 7 JSON files per folder:

| Scenario | "Today" | What it is built to test |
|---|---|---|
| `quiet` | 2026-07-02 | A normal month with about $1,200 of slack. Should need little. |
| `birthday` | 2026-10-03 | A birthday on the calendar (no cost listed). Last October's history has a $260 dinner and a $180 outfit. |
| `over_budget` | 2026-12-02 | A booked $1,350 wedding trip, an unknown-cost holiday trip, and $400 of gifts last December. Bills, goals and the wedding exceed income at typical spending. |
| `drift` | 2026-08-03 | Eating out creeps up about 5% every month ($216 to $378) and never passes her $400 limit. |

The scenario name only selects the data folder. It is never sent to the model, and the data files contain no hints about what the answer should be.

## How it works

```
question ──> model (my code calls the API) ──> "THOUGHT: ... ACTION: get_calendar({...})"
                  ^                                        |
                  |                                        v
            RESULT: {json}  <──  my code runs the tool, returns facts only
                  ...repeat until "FINAL: ..." or 25 steps...
FINAL answer ──> my code reads the allocation JSON and runs five checks (flags only)
```

* **`agent.py`** is the loop. It sends the system prompt and the question, reads the first `ACTION:` or `FINAL:` line, parses the arguments with `json.loads` (never `eval`), runs the tool, and feeds the result back. It is a generator, so every step is printed live, and each run is saved as a JSON log (question, every tool call and result, the final answer, step count, tokens). Hard step cap: `MAX_STEPS = 25`. A stop sequence on `RESULT:` stops the model from inventing tool results.
* **`tools.py`** has nine tools. They return **facts only** (numbers, dates, what the user said). They never say what something means:

| Tool | Returns |
|---|---|
| `get_balance` | checking balance, income received, income expected and still to come |
| `get_recurring_expenses` | bills and subscriptions, due days, which are paid, totals |
| `get_transactions` | past purchases in a category and date range (max 50 rows) |
| `get_category_average` | a category's average and each month's total, over full months |
| `get_spending_summary` | every category's average over N full months, plus what it cost in the same month last year |
| `get_calendar` | events in a date range, with a cost only when it is a known fact |
| `get_goals` | targets, saved so far, amount remaining, months left |
| `get_priorities` | what the user *said* she cares about, word for word |
| `sum_amounts` | adds a list of numbers (so the model never adds in its head) |

  There is no `is_affordable()` or `recommend()`. Those would move the judgment into code and turn the agent into a script with a model wrapped around it.
* **`prompts.py`** is the system prompt: the reply format, when each tool is useful, and what a final answer must contain (including that **YES** means affordable without cutting or delaying anything, **TIGHT** means only by cutting or delaying something it must name, and **NO** means not without cutting essentials or going against a stated priority).
* **`checks.py`** runs **after** the model answers and only **flags**. It never fixes or rebalances. The model never sees it. The five checks: (1) the allocation adds up to expected income within $1; (2) every fixed bill is there at its real amount; (3) an `unfunded_usd` line is allowed only if fixed bills alone exceed income; (4) `unassigned` is at most 10% of income; (5) no category (fixed bills aside, which check 2 covers) is below half of what the same month cost last year when the gap is at least $100. The thresholds in checks 4 and 5 are arbitrary and written down as such.
* **`baseline.py`** is the control: plain if-statements, no model (see the comparison below).
* **`run_tests.py`** runs the ten final questions and saves one log per run in `logs/final/`.

## Which model I used, and why

I started with the cheapest current model, **Claude Haiku 5.5** (the project rule: use the cheapest model that can do the job). In the one run I did on the hardest month, `over_budget`, it **never opened the calendar, missed the $1,350 wedding, wrote "no shortfall", and put an extra $700 into entertainment**, and every check still passed (`logs/step7_over_budget_haiku_first_run.json`). I did not repeat that run, so it is one sample, but it was clear enough to escalate. **Claude Sonnet 5.5** found the wedding on its own with the same prompt, cut shopping to pay for it and said so. All final runs use Sonnet 5.5. It costs roughly 20 times more per run (about $0.05 to $0.14 a run, from token counts at the listed prices, against about $0.005 for Haiku), still pennies. Escalating only when the cheap model's judgment was clearly weak, and keeping the failed trace, is the point.

## One run, from tool result to decision to check

`over_budget`, allocation question (`logs/final/over_budget_20261012_103155_398.json`). The lines are copied from the log; `...` marks a cut, and the text in parentheses is my note:

```
[step 4] THOUGHT: December may have events or gift costs that compete for money, so I'll check the calendar.
[step 4] ACTION:  get_calendar({"start_date": "2026-12-02", "end_date": "2026-12-31"})
[step 4] RESULT:  ... "Sam and Jordan's wedding (Denver)", "known_cost_usd": 1350.0 ...
[step 7] sum_amounts(...) -> 8804.7        (typical month plus the wedding is $104.70 over income)
[step 8] THOUGHT: I'm over income, so I'll trim shopping and add a small gifts line ...
[step 8] sum_amounts(...) -> 8700.0

FINAL: The tradeoff I recommend is to cut shopping from a typical ~$447 to ~$193, which funds the
wedding and a small $150 holiday gifts line ... This protects your priorities: the $20,000 savings
goal (the $1,663 left to hit it), the Roth IRA, groceries, and Solidcore. Shopping is the only category set below its typical cost.

CHECKS: 2 problem(s) flagged
  FLAG below last year: 'gifts' is $150.00; the same month last year it cost $400.00
  FLAG below last year: 'shopping' is $192.51; the same month last year it cost $510.63
```

The tool returned a fact (a $1,350 booked cost). The model decided what to cut and what to protect, using Maya's stated priorities. My code, independently, checked the arithmetic and flagged that two lines are far below last year. A flag is for a human to read, not a verdict: shopping was a deliberate, disclosed cut.

## Results: the ten final runs (Sonnet 5.5, `logs/final/`)

| # | Scenario / question | Result | Steps |
|---|---|---|---|
| 1 | `quiet` allocation | Sensible. Spare $1,150.73 went mostly to savings, some to entertainment and eating out. | 10 |
| 2 | `birthday` allocation | Raised eating out to $375 and entertainment to $200 for the birthday. Never cited last October's $547. | 10 |
| 3 | `over_budget` allocation | Found the wedding, cut shopping $447 to $193 and said so. Checks flagged gifts and shopping. | 9 |
| 4 | `drift` allocation | **Missed the trend.** Eating out set to $400. Never mentioned that it climbs every month. | 10 |
| 5 | `quiet`: $400 trip | **YES** ($2,850.73 left) | 9 |
| 6 | `over_budget`: $300 night out | **YES** ($1,571.54 left, wedding counted), with a caveat that eating out could pass her $400 limit | 9 |
| 7 | `quiet`: $25 lunch | **YES**. Skipped the calendar and priorities. | 6 |
| 8 | `quiet`: $2,500 laptop | **YES** ($750.73 left) | 8 |
| 9 | `over_budget`: $2,500 laptop | **TIGHT** (-$628.46). Said to cut all shopping plus $181.25 elsewhere, protecting savings, Roth, groceries and Solidcore. | 9 |
| 10 | `over_budget`: $6,000 vacation | **NO**. Still $832.60 short after cutting every discretionary category. Did not open the calendar. | 9 |

The same $2,500 laptop gets **YES in `quiet` and TIGHT in `over_budget`**: same purchase, different month, different verdict. Runs 1 to 8 cost about $0.71 and runs 9 and 10 about $0.19. (`logs/final/summary.json` covers runs 1 to 8 only.)

## The baseline: where the model earns its place, and where it doesn't

`baseline.py` uses plain if-statements, deliberately fair (it uses the real 6-month averages): pay every bill and subscription, give each everyday category its average, send what is left to savings, and call a purchase affordable if its price fits in what is left of this month's income after a 20% savings share. Output: `logs/baseline_comparison.txt`.

* **`over_budget` is where the model matters.** The baseline cannot see the calendar, so its plan has no $1,350 wedding: it adds up to $8,700 and looks tidy, but it is unrealistic by $1,350. It also sends $3,533 to savings against a goal that needs only $1,663. The agent budgets the wedding, funds exactly what the goal still needs, and cuts shopping.
* **Purchases:** the baseline and the agent agree on 4 of 6 questions. They differ on both laptops. For the `over_budget` laptop the baseline can only say NO; the agent says TIGHT and names what to cut. For the `quiet` laptop the baseline says NO and the agent says YES, but that is a **definition** difference, not intelligence: the baseline compares the price with this month's income, the agent counts cash on hand including $2,100 carried over.
* **`quiet`, `birthday`, `drift` allocations:** the differences are judgment calls following Maya's priorities (the agent keeps her Roth IRA line, the baseline has none), not clear wins. On `drift`, **both miss the trend**, and the baseline is arguably more careful ($333.52 for eating out against the agent's $400).

So the baseline does not match the agent in every month, which means the scenarios are not trivially easy. But where only averages matter, a rule does about as well.

## What I verified

* **The data:** re-running the generator twice gives byte-identical files; a search of the data for scenario labels or hints found none; the numbers match my plan.
* **Every tool, by hand,** against the JSON files: normal cases, empty cases (no events, empty list), weird input (a capital letter in a category, a US-style date, `num_months` of 0 or "six", text instead of a number, the forbidden tool name `is_affordable`) and boundaries. Bad input returns an `error` instead of crashing.
* **The checks, with fake bad allocations:** one adding to $9,500, rent cut to $2,000, a missing phone bill, 15.2% unassigned, an unfunded line when bills fit.
* **The loop, offline, with a scripted fake model** (no API cost): garbled replies count as a step, a fake `RESULT:` line after an action is ignored, the scenario name is never in the prompt, a model that never finishes stops at exactly 25 calls, a cut-off reply is flagged.
* **The model's arithmetic,** by adding up its final allocations myself. They add to exactly $8,700, and the model computes its totals with `sum_amounts`.
* **Not tested on the real API:** the real 401 (bad key), 404 (bad model name) and 429 (rate limit) messages. The step cap is tested only with the fake model, because no real run came near 25 steps.
* A second AI chat acted as a reviewer of the data, prompts and traces.

## What I caught by running it (and what I changed)

1. **A tidy plan that did not work.** The first `quiet` run passed every check, but about $810 a month of normal spending (transport, shopping, entertainment, health) had no line. Cause: no tool lists the categories, so the model could not ask for ones it did not know existed. Fix: I added `get_spending_summary`. (Claude Code recommended skipping it because of the deadline; I decided to add it anyway.)
2. **The cheap model failed the hard month** (see the model section). Fix: escalate to Sonnet 5.5.
3. **A 6-month window hid last December's $400 of gifts.** Both models asked for 6 months, so gifts looked like $0, and one answer said "you normally spend nothing here", which is false. Fix: the summary also returns what each category cost in the same month last year. I chose a tool field over a prompt rule ("check last year") because a rule would make every run do the same lookup.
4. **Purchase answers had no instruction to look up what is already committed.** After I added one sentence, the calendar was opened in every `over_budget` purchase run that followed, except one. The AI analysis (Claude Code, repeated by the second reviewer) first called the old YES answer wrong, using a cushion of about -$409. On re-checking, Claude Code found that figure used income only and ignored the checking balance, so "wrong" depended on a definition nobody had chosen. The allocation answer uses income only (by design) and the purchase answer uses cash flow, so they can disagree in the same month. I decided that "afford" means cash flow and put that definition in the prompt.
5. **A check that missed by a boundary.** Check 5 says "below half". The model put gifts at exactly half of last year's $400, so it did not fire. I left the number alone: it is arbitrary, and moving it because one run landed on its edge would be tuning to the trace.
6. **The TIGHT and NO verdicts had never appeared** in any purchase run, so I added two `over_budget` questions to test whether TIGHT and NO ever appear. They did.
7. **Errors in my own setup, caught in review:** a prompt line ("only use numbers that came from a tool result") contradicted allocating, a wedding note said "paid this month" when nothing was paid, and the transport spending was labelled "gas" while my definition of essentials said "transport".

## Known limits

* **One run per question.** The model varies from run to run (one answer labelled its $150 gifts line "a guess", another did not; the $6,000 run skipped the calendar). These are samples, not measurements.
* **Drift was missed in every run.** The model had the numbers (a 6-month average of $333.52 against $216.26 for the same month last year) and said nothing. I think adding the summary tool may have made it less likely to compare month by month, but I never ran `drift` before that tool existed, so that is a guess. Two possible fixes: return monthly totals (or just the most recent month) in the summary tool, which is a plain fact, or add a rule telling the model to report trends, which would be a hint. I tried neither because of time, and since the model already had a signal and ignored it, more data alone may not change the answer.
* **The path varies with the question, not with the month.** The $25 lunch used 4 lookups and 6 steps, but the four allocation runs used the same six lookups (9 to 10 steps). That meets the requirement that the path varies only partly.
* **Last year's numbers reach the model but rarely the answer.** In the main set of eight runs none of the final answers mentioned them; the `over_budget` laptop run did. Nothing in the prompt asks for it.
* **The checks test numbers, not reasoning.** They cannot tell whether an explanation is right. Check 3 (`unfunded_usd`) was only hand-tested, since no scenario makes fixed bills exceed income.
* **Purchase verdicts are monthly, not day by day.** There is no paycheck schedule, so "can I pay this today" is out of scope.
* The tool protocol (`ACTION:` / `FINAL:` text, parsed by my own code) is deliberately simple so I can explain every line; native API tool calling would be more robust.
* It is a class project on invented data, not financial advice.

## How I used AI to build this

I wrote the requirements and rules in `CLAUDE.md` first (what counts as an agent, tools return facts only, no framework, step cap, synthetic data, small commits). Then I built it with **Claude Code** (Claude), one step at a time: plan, data generator, tools, loop, runs, baseline, README. For each step it explained what it would do, I read the result, tested it by hand and committed. I made the design decisions (the fictional budget and priorities, adding the summary tool, defining "afford" as cash flow, the ladder questions) and rejected recommendations when I disagreed. A second AI chat reviewed the work and found real problems (listed above). `CLAUDE.md` is the running log: it records 57 numbered decisions, including the mistakes and corrections.

## Where things are

| Path | What it is |
|---|---|
| `agent.py` | the loop (main file) |
| `tools.py` | the nine fact-only tools |
| `prompts.py` | the system prompt |
| `checks.py` | the five checks (flag only) |
| `baseline.py` | the rule-based control |
| `run_tests.py` | the ten final questions |
| `generate_data.py`, `data/` | the synthetic data and its generator |
| `logs/final/` | the ten final runs |
| `logs/first_set_before_purchase_rule/`, `logs/repeats_purchase_rule/` | earlier runs kept as evidence |
| `logs/step5_*`, `logs/step7_*` | the early traces (the Haiku failure, the `quiet` runs before and after the fixes) |
| `logs/baseline_comparison.txt` | the baseline output |
| `CLAUDE.md` | my project notes and every decision |
| `.env.example` | setting names only; the real `.env` is never committed |

## The seven requirements, checked honestly

| Requirement | Status |
|---|---|
| My own code calls the model (Anthropic SDK) | Yes (`agent.py`) |
| The path varies | Partly (see limits) |
| Real judgment an if-statement could not capture | Yes in places (the `over_budget` cut, TIGHT with named cuts); not consistently |
| Tools return facts only | Yes |
| No framework | Yes (`anthropic` and `python-dotenv` only) |
| Hard step cap | Yes (25; tested with the fake model) |
| No secrets in the repo | Yes (`.env` is git-ignored; I checked `git ls-files` before every push) |
