# Assignment 1: GitHub repository and AI-assisted code translation

Student: Anay Sharma

This directory contains an ATS implementation of the eight-queens puzzle and a Python 3 translation of that program.

## Files

- `queens.dats` — original ATS from the textbook excerpt the professor posted on Piazza.
- `queens.py` — Python 3 translation of those functions.
- `test_queens.py` — AI-generated tests of the top-level functions (not part of the translation).
- `TEST-RESULTS.md` — test cases and results.
- `AI-TRANSCRIPT.md` — prompts and review notes from the AI session.

## How to run

Python 3:

```text
python queens.py
python test_queens.py
```

The ATS original is meant to be built with the ATS2 compiler, for example:

```text
patscc -o queens queens.dats
./queens
```

`patscc` was not available on the machine used for this assignment, so the original was checked against the textbook’s first printed solution and the stated total of 92 solutions.

## Source

https://ats-lang.github.io/FROZEN000/DOCUMENT/INT2PROGINATS/HTML/INT2PROGINATS-BOOK-onechunk.html#example-the-eight-queens-puzzle

## AI Reflection

The AI (Cursor) was useful as a first-pass translator. It mapped the ATS helpers almost line-for-line: an 8-tuple board, `board_get` / `board_set` as explicit index cases, `safety_test1` / `safety_test2`, the same DFS order, and the same print layout (`". "` and `"Q "`). That closeness made it possible to compare the Python against the book instead of rewriting eight queens from scratch.

The important mistake was semantic, not syntactic. ATS turns tail-recursive `search` into a loop. Python does not. The first translation therefore printed the documented first solution and then died with `RecursionError` before finishing the 92 boards. Trusting the draft without running it would have looked plausible: the first board matched the textbook, the helpers looked right, and `main` still asserted `nsol == 92`. The crash only showed up when the program was actually executed.

To check the translation I had to understand the original DFS, not just the chess rules. When a queen is placed on the last row, `search` continues from the *previous* board and `j+1`, not from `bd1`. `board_get` on an invalid index returns `~1` (Python `-1`) in the text the professor posted. Print format matters: ATS `print!` concatenates pieces, so `"Solution #"` plus a number should not pick up extra spaces from Python's default `print`. I also needed the count of 92 solutions and the first printed board from the book, because I could not compile ATS here.

The generated version could not have been trusted without testing. After the tail-call fix, tests cover the top-level functions: printers, `board_get` / `board_set`, both safety tests, and `search`. AI shortened the mechanical rewrite and helped keep the control flow aligned with ATS. It did not remove the need to know what the original program does, to watch for language differences, or to treat the output as a draft until it was run and compared.
