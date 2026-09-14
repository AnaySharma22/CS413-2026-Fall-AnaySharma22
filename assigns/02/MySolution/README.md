# Assignment 2: LAMBDA0 pairs and eight-queens translation

Student: Anay Sharma

## Files

| File | Role |
| --- | --- |
| `lambda0.py` | Extended interpreter (pairs, projections, comparisons) |
| `queens.dats` | Original ATS2 eight-queens source (Assignment 1 / Piazza text) |
| `queens_lambda0.py` | Closed LAMBDA0 encoding of that program |
| `TEST/test01_lambda0.py` | Starter CBV tests, run against this `lambda0.py` |
| `TEST/test02_lambda0.py` | Tests for pairs / projections |
| `TEST/test03_queens.py` | Tests for the queens translation |

## How to run

From `assigns/02/MySolution`:

```text
python TEST/test01_lambda0.py
python TEST/test02_lambda0.py
python TEST/test03_queens.py
python queens_lambda0.py
```

## Part 1–2: pairs and projections

Added cases for `T0Mpair`, `T0Mpfst`, and `T0Mpsnd` in:

- `t0erm_size`, `t0erm_fvset`, `t0erm_subst0`
- `t0erm_cbv_evaluate0` (left-to-right pair evaluation; projections require a pair value)

Also added primitives needed by the queens term (documented as interpreter extensions, not part of the starter):

- unary `abs`
- comparisons `<`, `<=`, `>`, `>=`, `=`, `!=` producing `T0Mbtf`

## Part 3: eight-queens as a LAMBDA0 term

### Mapping from ATS2

| ATS2 | LAMBDA0 |
| --- | --- |
| `int8` tuple of columns | Nested pairs `pair(c0, pair(c1, … nil))` with `nil = -1` |
| `board_get` / `board_set` | Unrolled `if i = 0/1/…` chains (same idea as the ATS if-ladder) |
| `safety_test1` | Curried `T0Mlam` using `!=` and `abs` |
| `safety_test2` | `T0Mfix` over earlier rows |
| `search` | `T0Mfix` with args packed as nested pairs `(bd, i, j, nsol)` |

Python only builds the AST and decodes the result. The DFS and conflict checks run inside `t0erm_cbv_evaluate0`.

### Comparison with the original

| Check | ATS2 / known | LAMBDA0 |
| --- | --- | --- |
| Solutions for N=1,4,5 | 1, 2, 10 | same counts |
| First N=8 board | `(0,4,7,5,2,6,1,3)` | same board from `first_solution(8)` |

### Call-by-value limitation

Substitution-based CBV re-embeds the entire `T0Mfix` AST on every recursive call. Counting all 92 solutions for N=8 grows too large (`RecursionError`). The submitted program therefore counts small N fully and, for N=8, runs a first-solution search in LAMBDA0 (still the same safety/search logic). `sys.setrecursionlimit` is raised for that search.

## AI review notes

Cursor helped draft the pair cases and the queens AST builders. I checked:

- Pair evaluation order and unused-component evaluation (assignment examples)
- That search/safety live in the term, not in Python loops
- Known N-queens totals and the textbook first N=8 board
- Starter `test01` still passes on the extended interpreter
