"""
agent.py: the loop. This is the main file of the project.

Why it exists: it is the part that makes this an agent. It sends the question to the
model, reads the reply, runs the tool the model asked for, feeds the result back, and
repeats until the model gives a FINAL answer or the step cap is reached. My own code
makes every API call (Anthropic SDK, no framework).

Run:  python3 agent.py <scenario> "<question>"
The scenario name only picks the data folder. It is never sent to the model.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from checks import check_scenario, extract_allocation
from narrate import narrate
from prompts import build_system_prompt
from tools import run_tool

MAX_STEPS = 25                 # hard cap: every step is a paid API call
MAX_TOKENS = 2000              # per reply; too low silently cuts the answer off
MAX_RETRIES = 3                # the SDK retries 429s and server errors with backoff
STOP_SEQUENCES = ["RESULT:"]   # cuts the model off if it starts writing a fake tool result
SHOW_RESULT_CHARS = 400        # how much of a tool result to print (the log keeps all of it)

ROOT = Path(__file__).parent
DATA_ROOT = ROOT / "data"
LOG_DIR = ROOT / "logs" / "scratch"   # throwaway runs; keeper logs go in logs/
ACTION_PATTERN = re.compile(r"^ACTION:\s*(\w+)\s*\((.*)\)\s*$")


def load_settings():
    """Read .env and return the model name. The API key is checked but never printed."""
    load_dotenv(ROOT / ".env")
    model = os.getenv("MODEL_NAME")
    if not os.getenv("ANTHROPIC_API_KEY") or not model:
        sys.exit("Missing ANTHROPIC_API_KEY or MODEL_NAME. Copy .env.example to .env and fill both in.")
    return model


def find_thought(text):
    """The model's one-line THOUGHT, for display. The code never acts on it."""
    for line in text.splitlines():
        if line.strip().startswith("THOUGHT:"):
            return line.strip()[len("THOUGHT:"):].strip()
    return ""


def parse_reply(text):
    """Read the first ACTION: or FINAL: line. Never uses eval; arguments go through json.loads."""
    lines = text.strip().splitlines()
    for i, raw in enumerate(lines):
        line = raw.strip()
        if line.startswith("FINAL:"):
            body = [line[len("FINAL:"):].strip()] + lines[i + 1:]
            return {"kind": "final", "text": "\n".join(body).strip()}
        if line.startswith("ACTION:"):
            match = ACTION_PATTERN.match(line)
            if not match:
                return {"kind": "bad", "reason": "the ACTION line must look like ACTION: tool_name({...})"}
            try:
                args = json.loads(match.group(2).strip() or "{}")
            except json.JSONDecodeError:
                return {"kind": "bad", "reason": "the arguments are not valid JSON"}
            return {"kind": "action", "tool": match.group(1), "args": args}
    return {"kind": "bad", "reason": "the reply had neither an ACTION: line nor a FINAL: line"}


def describe_api_error(problem):
    """A short, clear message for each kind of API failure (most specific first)."""
    if isinstance(problem, anthropic.AuthenticationError):
        return "401: the API key was rejected. Check ANTHROPIC_API_KEY in .env."
    if isinstance(problem, anthropic.NotFoundError):
        return "404: model not found. Check MODEL_NAME in .env against the Models page on docs.claude.com."
    if isinstance(problem, anthropic.RateLimitError):
        return "429: rate limited even after retries. Wait a minute and run again."
    if isinstance(problem, anthropic.APIStatusError):
        return f"API error {problem.status_code}: {problem.message}"
    return "Network problem reaching the API. Check your internet connection."


def run_agent(scenario, question, model, log_dir=LOG_DIR):
    """The loop, as a generator: yields one event at a time, then writes the run log."""
    data_dir = str(DATA_ROOT / scenario)
    today = json.loads((DATA_ROOT / scenario / "scenario.json").read_text())["today"]
    system = build_system_prompt(today)
    client = anthropic.Anthropic(max_retries=MAX_RETRIES)
    messages = [{"role": "user", "content": question}]
    tokens = {"input": 0, "output": 0}
    steps, flags, allocation = [], [], None
    final_text, error, outcome = None, None, "step cap"

    for step in range(1, MAX_STEPS + 1):
        try:
            response = client.messages.create(model=model, max_tokens=MAX_TOKENS, system=system,
                                              messages=messages, stop_sequences=STOP_SEQUENCES)
        except (anthropic.APIStatusError, anthropic.APIConnectionError) as problem:
            error, outcome = describe_api_error(problem), "error"
            yield {"type": "error", "step": step, "message": error}
            break
        tokens["input"] += response.usage.input_tokens
        tokens["output"] += response.usage.output_tokens
        if response.stop_reason == "refusal":
            error, outcome = "The model declined to answer (refusal).", "refused"
            yield {"type": "error", "step": step, "message": error}
            break
        cut_off = response.stop_reason == "max_tokens"
        if cut_off:
            yield {"type": "warning", "step": step,
                   "message": f"reply was cut off at MAX_TOKENS ({MAX_TOKENS}); thinking tokens count too"}

        text = "".join(block.text for block in response.content if block.type == "text")
        messages.append({"role": "assistant", "content": response.content})  # kept unchanged
        reply, thought = parse_reply(text), find_thought(text)
        entry = {"step": step, "thought": thought, "reply": text}

        if reply["kind"] == "final":
            final_text, outcome = reply["text"], "final"
            yield {"type": "final", "step": step, "thought": thought, "text": final_text}
            allocation, problem = extract_allocation(final_text)
            note = ""
            if problem:
                flags.append(f"FLAG allocation block: {problem}")
            elif allocation is None:
                note = "no allocation block (normal for a purchase question)"
            else:
                flags = check_scenario(data_dir, allocation)  # only flags; never changes the numbers
            if cut_off:
                flags.append(f"FLAG cut off: the answer hit MAX_TOKENS ({MAX_TOKENS}) and may be incomplete")
            steps.append(entry)
            yield {"type": "checks", "flags": flags, "note": note}
            break

        if reply["kind"] == "action":
            yield {"type": "action", "step": step, "thought": thought, "tool": reply["tool"], "args": reply["args"]}
            feedback = run_tool(data_dir, reply["tool"], reply["args"])
            entry.update(tool=reply["tool"], args=reply["args"], result=feedback)
            yield {"type": "result", "step": step, "result": feedback, "tool": reply["tool"], "args": reply["args"]}
        else:  # a garbled reply still counts as a step, so the cap always applies
            entry["problem"] = reply["reason"]
            yield {"type": "bad_reply", "step": step, "message": reply["reason"]}
            feedback = {"error": reply["reason"] + ". Reply with a THOUGHT: line, then one ACTION: or FINAL: line."}
        steps.append(entry)
        messages.append({"role": "user", "content": "RESULT: " + json.dumps(feedback)})

    if outcome == "step cap":
        yield {"type": "error", "step": MAX_STEPS, "message": f"hit the step cap ({MAX_STEPS}) without a FINAL answer"}

    log = {"scenario": scenario, "question": question, "model": model, "today_in_scenario": today,
           "outcome": outcome, "error": error, "steps_used": len(steps), "tokens": tokens,
           "steps": steps, "final_answer": final_text, "allocation": allocation, "flags": flags}
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # real clock, to the millisecond: file name only
    log_path = log_dir / f"{scenario}_{stamp}.json"
    log_path.write_text(json.dumps(log, indent=2) + "\n")
    yield {"type": "done", "outcome": outcome, "steps": len(steps), "tokens": tokens, "log_path": str(log_path)}


def show(event):
    """Print one event. These printed steps are the live demo."""
    kind, step = event["type"], event.get("step")
    if kind in ("action", "final") and event["thought"]:
        print(f"\n[step {step}] THOUGHT: {event['thought']}")
    if kind == "action":
        print(f"[step {step}] ACTION:  {event['tool']}({json.dumps(event['args'])})")
    elif kind == "result":
        text = json.dumps(event["result"])
        print(f"[step {step}] RESULT:  {text[:SHOW_RESULT_CHARS]}{' ...' if len(text) > SHOW_RESULT_CHARS else ''}")
        print(f"[step {step}] IN PLAIN ENGLISH: {narrate(event['tool'], event['args'], event['result'])}")
    elif kind == "final":
        print(f"\n[step {step}] FINAL ANSWER:\n{event['text']}")
    elif kind == "checks":
        summary = event["note"] or ("all passed" if not event["flags"] else f"{len(event['flags'])} problem(s) flagged")
        print("\nCHECKS:", summary)
        for flag in event["flags"]:
            print(" ", flag)
    elif kind in ("warning", "bad_reply", "error"):
        print(f"\n[step {step}] {kind.upper()}: {event['message']}")
    elif kind == "done":
        used = event["tokens"]
        print(f"\nRun ended: {event['outcome']} after {event['steps']} steps. "
              f"Tokens: {used['input']:,} in / {used['output']:,} out. Log: {event['log_path']}")


def main():
    scenarios = sorted(p.name for p in DATA_ROOT.iterdir() if p.is_dir())
    if len(sys.argv) != 3 or sys.argv[1] not in scenarios:
        sys.exit(f'Usage: python3 agent.py <scenario> "<question>"\nScenarios: {", ".join(scenarios)}')
    model = load_settings()
    for event in run_agent(sys.argv[1], sys.argv[2], model):
        show(event)


if __name__ == "__main__":
    main()
