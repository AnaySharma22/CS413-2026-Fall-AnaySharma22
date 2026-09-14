"""Tests for the eight-queens LAMBDA0 translation.

Run with: python TEST/test03_queens.py
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lambda0 import (
    T0Mint, T0Mbtf, T0Mapp, T0Mpair,
    t0erm_cbv_evaluate0, t0erm_fvset,
)
from queens_lambda0 import (
    App, safety_test1_term, safety_test2_term, board_get_term,
    make_board, count_solutions, first_solution, is_safe_placement,
    queens_count_term, queens_first_term, KNOWN_COUNTS, FIRST_SOLUTION_N8,
    I,
)


class TestConflictLogic(unittest.TestCase):
    def test_safety_test1_same_column(self):
        term = App(safety_test1_term(), I(0), I(3), I(1), I(3))
        self.assertEqual(t0erm_cbv_evaluate0(term), T0Mbtf(False))

    def test_safety_test1_same_diagonal(self):
        term = App(safety_test1_term(), I(0), I(0), I(1), I(1))
        self.assertEqual(t0erm_cbv_evaluate0(term), T0Mbtf(False))

    def test_safety_test1_safe(self):
        term = App(safety_test1_term(), I(0), I(0), I(1), I(2))
        self.assertEqual(t0erm_cbv_evaluate0(term), T0Mbtf(True))

    def test_safety_test2_against_earlier_rows(self):
        get_t = board_get_term(4)
        st2 = safety_test2_term(get_t)
        # Board with queen at row 0, col 0. Placing at (1,2) is safe.
        bd = make_board([0, 0, 0, 0])
        args = T0Mpair(T0Mpair(I(1), I(2)), T0Mpair(bd, I(0)))
        self.assertEqual(t0erm_cbv_evaluate0(App(st2, args)), T0Mbtf(True))
        # Placing at (1,0) shares a column with row 0.
        args_bad = T0Mpair(T0Mpair(I(1), I(0)), T0Mpair(bd, I(0)))
        self.assertEqual(t0erm_cbv_evaluate0(App(st2, args_bad)), T0Mbtf(False))


class TestSmallBoards(unittest.TestCase):
    def test_counts(self):
        for n in (1, 2, 3, 4, 5):
            with self.subTest(n=n):
                self.assertEqual(count_solutions(n), KNOWN_COUNTS[n])

    def test_count_terms_are_closed(self):
        for n in (1, 4):
            self.assertEqual(t0erm_fvset(queens_count_term(n)), frozenset())


class TestEightQueensFirstSolution(unittest.TestCase):
    def test_first_board_matches_ats2(self):
        board = first_solution(8)
        self.assertEqual(board, FIRST_SOLUTION_N8)
        self.assertTrue(is_safe_placement(board))

    def test_first_term_is_closed(self):
        self.assertEqual(t0erm_fvset(queens_first_term(8)), frozenset())

    def test_no_shared_row_column_or_diagonal(self):
        board = first_solution(8)
        assert board is not None
        self.assertEqual(len(board), 8)
        self.assertEqual(len(set(board)), 8)
        self.assertTrue(is_safe_placement(board))


if __name__ == "__main__":
    unittest.main(verbosity=2)
