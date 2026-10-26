"""Command-line demonstration. From assigns/06:

python MySolution/demo.py

Each program is compiled, its pure term is written to demo-out/NN.lam, the
term is run under the execution budget, and a value is observed under the
separate observation budget. Terminating programs are also run on the source
side by the same evaluator, and the two answers are compared.
"""

from __future__ import annotations

from pathlib import Path

import boot  # noqa: F401  (adds assigns/05 to sys.path)

from compile import compile_expr
from evaluate import evaluate, source_data
from examples import demonstrations
from observe import observe
from target import pretty
from visitors import d0exp_pretty

# Terminating programs finish far below these: the largest, Fibonacci of 5,
# needs 3,080 execution steps and factorial of 4 needs 333 observation steps.
EXEC_BUDGET = 20000
OBS_BUDGET = 5000
# The diverging programs are stopped at a small budget so exhaustion is shown
# quickly. Exhaustion is not a proof that they never return.
EXHAUST_BUDGET = 200
INLINE_LIMIT = 220
OUT = Path(__file__).resolve().parent / "demo-out"


def run_example(expr, kind, exec_budget: int, obs_budget: int):
    term = compile_expr(expr)
    reduced = evaluate(term, exec_budget)
    seen = None
    if kind is not None and reduced.status == "value":
        seen = observe(reduced.value, kind, obs_budget)
    return term, reduced, seen


def main() -> None:
    OUT.mkdir(exist_ok=True)
    print(f"Execution budget {EXEC_BUDGET}. Observation budget {OBS_BUDGET}.")
    print(f"Diverging programs use execution budget {EXHAUST_BUDGET}.")
    print(f"Every pure term is saved in {OUT.name}/.")
    agreed = 0
    for index, (title, expr, kind, expected) in enumerate(demonstrations(), start=1):
        exec_budget = EXHAUST_BUDGET if kind is None else EXEC_BUDGET
        term, reduced, seen = run_example(expr, kind, exec_budget, OBS_BUDGET)
        text = pretty(term)
        filename = OUT / f"{index:02d}.lam"
        filename.write_text(text + "\n", encoding="utf-8")
        print()
        print(f"== {index:02d}. {title}")
        print(f"source:      {d0exp_pretty(expr)}")
        if len(text) <= INLINE_LIMIT:
            print(f"target:      {text}")
        print(f"target file: {OUT.name}/{filename.name} ({len(text)} characters)")
        print(
            f"execution:   {reduced.status}, {reduced.steps} beta-value steps"
            f" (budget {exec_budget})"
        )
        if kind is None:
            print("observation: not run, because execution did not reach a value")
            print("expected:    budget exhaustion")
            ok = reduced.status == "exhausted"
        else:
            source = source_data(evaluate(expr))
            print(
                f"observation: {seen.status}, {seen.steps} beta-value steps"
                f" (budget {OBS_BUDGET}), kind {kind}"
            )
            print(f"decoded:     {seen.value}")
            print(f"source side: {source}")
            print(f"expected:    {expected}")
            ok = seen.status == "value" and seen.value == expected == source
        agreed += ok
        print(f"agrees:      {'yes' if ok else 'NO'}")
    print()
    print(f"{agreed} of {len(demonstrations())} programs match the expected column.")


if __name__ == "__main__":
    main()
