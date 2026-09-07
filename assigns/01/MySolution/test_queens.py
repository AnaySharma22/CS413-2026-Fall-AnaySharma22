"""Tests for the Python translation of the ATS eight-queens program."""

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


def is_safe_board(bd):
    for i0 in range(8):
        for i1 in range(i0):
            if not queens.safety_test1(i0, bd[i0], i1, bd[i1]):
                return False
    return True


class EightQueensTests(unittest.TestCase):
    def test_normal_solution_count_and_first_board(self):
        """Normal case: full 8-queens search from an empty board."""
        solutions = []
        nsol = queens.search((0, 0, 0, 0, 0, 0, 0, 0), 0, 0, 0, verbose=False, solutions=solutions)
        self.assertEqual(nsol, 92)
        self.assertEqual(len(solutions), 92)
        self.assertEqual(solutions[0], FIRST_SOLUTION)

    def test_boundary_out_of_range_and_unsafe_placements(self):
        """Boundary / unusual cases: invalid index, same column, same diagonal."""
        empty = (0, 0, 0, 0, 0, 0, 0, 0)
        self.assertEqual(queens.board_get(empty, -1), 0)
        self.assertEqual(queens.board_get(empty, 8), 0)
        self.assertFalse(queens.safety_test1(0, 3, 1, 3))
        self.assertFalse(queens.safety_test1(0, 0, 1, 1))
        self.assertTrue(queens.safety_test1(0, 0, 1, 2))
        self.assertTrue(queens.safety_test2(0, 0, empty, -1))

    def test_additional_every_solution_is_safe(self):
        """Additional case: every reported solution is a valid 8-queens board."""
        solutions = []
        queens.search((0, 0, 0, 0, 0, 0, 0, 0), 0, 0, 0, verbose=False, solutions=solutions)
        columns = [tuple(bd) for bd in solutions]
        self.assertEqual(len(set(columns)), 92)
        for bd in solutions:
            self.assertEqual(len(set(bd)), 8)
            self.assertTrue(is_safe_board(bd))

    def test_print_board_matches_book_example(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            queens.print_board((0, 1, 2, 3, 4, 5, 6, 7))
        self.assertEqual(buf.getvalue(), DIAGONAL_BOARD)


if __name__ == "__main__":
    unittest.main()
