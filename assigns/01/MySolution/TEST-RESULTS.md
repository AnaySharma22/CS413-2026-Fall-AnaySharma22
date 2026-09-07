# Test results

 Python tests cover the **top-level functions** from the source the professor posted (not extra search-from-partial-board behavior). Testing code is not part of the translation.

## How to run

```text
python queens.py
python test_queens.py
```

## Tests of top-level functions

| Function | Kind | Case | Result |
| --- | --- | --- | --- |
| `print_dots` | boundary | `i = 0` prints nothing | pass |
| `print_dots` | normal | `i = 3` prints `". . . "` | pass |
| `print_row` | normal | column 0 and column 7 rows | pass |
| `print_board` | normal | diagonal board from the textbook | pass |
| `board_get` | normal | each of the eight tuple fields | pass |
| `board_get` | boundary | index `-1` and `8` return `-1` (`~1`) | pass |
| `board_set` | normal | set row 3 to column 5 | pass |
| `board_set` | boundary | invalid row returns the same tuple | pass |
| `safety_test1` | normal | safe placement is true | pass |
| `safety_test1` | unusual | same column or same diagonal is false | pass |
| `safety_test2` | boundary | `i = -1` is true | pass |
| `safety_test2` | normal | conflict / no conflict with an earlier queen | pass |
| `search` | normal | empty board → 92 solutions; first board matches the book | pass |
| `search` | boundary | `j = N` on row 0 returns the incoming `nsol` | pass |
| `search` | additional | all 92 boards are pairwise safe | pass |

## Command log

```text
python test_queens.py
```

Result: `Ran 18 tests in 0.038s` — `OK`
