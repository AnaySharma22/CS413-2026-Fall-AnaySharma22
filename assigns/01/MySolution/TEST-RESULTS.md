# Test results

ATS (`patscc` / `atsopt`) is not installed in this environment, so the original program was not compiled here. The Python translation was checked against the behavior documented in *Introduction to Programming in ATS* (the first printed solution and the claim that there are 92 solutions) and against the `main0` assertion `nsol = 92` in `queens.dats`.

## How to run

```text
python queens.py
python test_queens.py
```

`python queens.py` prints the diagonal starter board, then all 92 solutions, and asserts that the count is 92.

## Test cases

### 1. Normal input

Search from board `(0, 0, 0, 0, 0, 0, 0, 0)` at row 0, column 0, as in ATS `main0`.

| Check | Expected | Python result |
| --- | --- | --- |
| Number of solutions | 92 | 92 |
| First solution | `(0, 4, 7, 5, 2, 6, 1, 3)` matching the book board | match |

Book first solution:

```text
Q . . . . . . .
. . . . Q . . .
. . . . . . . Q
. . . . . Q . .
. . Q . . . . .
. . . . . . Q .
. Q . . . . . .
. . . Q . . . .
```

### 2. Boundary / unusual cases

| Case | Expected | Python result |
| --- | --- | --- |
| `board_get(bd, -1)` and `board_get(bd, 8)` | `0` (ATS `queens.dats` else-branch) | 0 |
| Two queens in the same column | `safety_test1` is false | false |
| Two queens on the same diagonal | `safety_test1` is false | false |
| `safety_test2(..., i=-1)` | true (no earlier rows) | true |

The original ATS `search` never starts from a completed board; these cases exercise helpers the search relies on at the edges of the DFS.

### 3. Additional test

Every one of the 92 boards has eight distinct columns, and `safety_test1` holds for every pair of queens.

| Check | Expected | Python result |
| --- | --- | --- |
| Unique boards | 92 | 92 |
| All boards legal | all safe | all safe |

### 4. Print format

`print_board((0, 1, 2, 3, 4, 5, 6, 7))` matches the eight-line example from the book (queen on the main diagonal, `". "` / `"Q "` cells, blank line after the board).

## Command log

```text
python test_queens.py
```

Result: `Ran 4 tests in 0.039s` — `OK`
