"""Tests for the top-level functions in the eight-queens translation.

These tests are not part of the translation. They were generated (and then
reviewed) to check print_dots, print_row, print_board, board_get, board_set,
safety_test1, safety_test2, and search.
"""

import io
import unittest
from contextlib import redirect_stdout

import queens


DIAGONAL_BOARD = """\
Q . . . . . . . 
. Q . . . . . . 
. . Q . . . . . 
. . . Q . . . . 
. . . . Q . . . 
. . . . . Q . . 
. . . . . . Q . 
. . . . . . . Q 

"""

FIRST_SOLUTION = (0, 4, 7, 5, 2, 6, 1, 3)
EMPTY = (0, 0, 0, 0, 0, 0, 0, 0)


class TestPrintDots(unittest.TestCase):
    def test_zero_prints_nothing(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            queens.print_dots(0)
        self.assertEqual(buf.getvalue(), "")

    def test_three_dots(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            queens.print_dots(3)
        self.assertEqual(buf.getvalue(), ". . . ")


class TestPrintRow(unittest.TestCase):
    def test_queen_in_column_zero(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            queens.print_row(0)
        self.assertEqual(buf.getvalue(), "Q . . . . . . . \n")

    def test_queen_in_last_column(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            queens.print_row(7)
        self.assertEqual(buf.getvalue(), ". . . . . . . Q \n")


class TestPrintBoard(unittest.TestCase):
    def test_diagonal_example_from_textbook(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            queens.print_board((0, 1, 2, 3, 4, 5, 6, 7))
        self.assertEqual(buf.getvalue(), DIAGONAL_BOARD)


class TestBoardGet(unittest.TestCase):
    def test_each_row(self):
        bd = (10, 11, 12, 13, 14, 15, 16, 17)
        for i, expected in enumerate(bd):
            self.assertEqual(queens.board_get(bd, i), expected)

    def test_out_of_range_is_negative_one(self):
        """Boundary: ATS else-branch is ~1."""
        self.assertEqual(queens.board_get(EMPTY, -1), -1)
        self.assertEqual(queens.board_get(EMPTY, 8), -1)


class TestBoardSet(unittest.TestCase):
    def test_set_middle_row(self):
        bd = queens.board_set(EMPTY, 3, 5)
        self.assertEqual(bd, (0, 0, 0, 5, 0, 0, 0, 0))
        self.assertEqual(queens.board_get(bd, 3), 5)

    def test_invalid_row_returns_same_board(self):
        bd = (1, 2, 3, 4, 5, 6, 7, 0)
        self.assertEqual(queens.board_set(bd, 8, 3), bd)
        self.assertEqual(queens.board_set(bd, -1, 3), bd)


class TestSafetyTest1(unittest.TestCase):
    def test_same_column_is_unsafe(self):
        self.assertFalse(queens.safety_test1(0, 3, 4, 3))

    def test_same_diagonal_is_unsafe(self):
        self.assertFalse(queens.safety_test1(0, 0, 1, 1))
        self.assertFalse(queens.safety_test1(2, 5, 4, 3))

    def test_safe_placement(self):
        self.assertTrue(queens.safety_test1(0, 0, 1, 2))


class TestSafetyTest2(unittest.TestCase):
    def test_no_earlier_rows(self):
        self.assertTrue(queens.safety_test2(0, 0, EMPTY, -1))

    def test_conflicts_with_an_earlier_queen(self):
        bd = queens.board_set(EMPTY, 0, 2)
        self.assertFalse(queens.safety_test2(1, 2, bd, 0))

    def test_safe_against_earlier_queens(self):
        bd = queens.board_set(EMPTY, 0, 0)
        self.assertTrue(queens.safety_test2(1, 2, bd, 0))


class TestSearch(unittest.TestCase):
    def test_normal_full_search(self):
        solutions = []
        nsol = queens.search(EMPTY, 0, 0, 0, verbose=False, solutions=solutions)
        self.assertEqual(nsol, 92)
        self.assertEqual(solutions[0], FIRST_SOLUTION)

    def test_boundary_finished_row_index_zero(self):
        """Unusual: j already equals N on row 0, so search returns nsol immediately."""
        self.assertEqual(queens.search(EMPTY, 0, queens.N, 7, verbose=False), 7)

    def test_additional_every_solution_is_safe(self):
        solutions = []
        queens.search(EMPTY, 0, 0, 0, verbose=False, solutions=solutions)
        self.assertEqual(len(set(solutions)), 92)
        for bd in solutions:
            self.assertEqual(len(set(bd)), 8)
            for i0 in range(8):
                for i1 in range(i0):
                    self.assertTrue(queens.safety_test1(i0, bd[i0], i1, bd[i1]))


if __name__ == "__main__":
    unittest.main()
