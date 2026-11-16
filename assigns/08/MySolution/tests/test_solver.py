"""LAMBDA3 CPS solver and lazy stream tests."""

from __future__ import annotations

import unittest

from support import QueensSolver

FOUR_SOLUTIONS = [[1, 3, 0, 2], [2, 0, 3, 1]]


class SolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.solver = QueensSolver()

    def take(self, size, limit=None, kinds=None):
        stream = self.solver.open_stream(size)
        self.assertTrue(self.solver.is_unevaluated(stream))
        events = []
        while True:
            event, stream, finished = self.solver.next_event(stream)
            if event is None:
                break
            events.append(event)
            if kinds is not None and event["event"] in kinds:
                pass
            if finished or (limit is not None and len(events) >= limit):
                break
        return events, stream

    def test_opening_does_not_force_the_stream(self):
        self.solver.counter.reset()
        stream = self.solver.open_stream(8)
        self.assertTrue(self.solver.is_unevaluated(stream))
        self.assertEqual(self.solver.counter.forces, 0)

    def test_forcing_one_cell_does_not_force_its_tail(self):
        self.solver.counter.reset()
        stream = self.solver.open_stream(5)
        event, tail, finished = self.solver.next_event(stream)
        self.assertEqual(event["event"], "try")
        self.assertFalse(finished)
        self.assertTrue(self.solver.is_unevaluated(tail))
        forces_after_one = self.solver.counter.forces
        self.assertGreaterEqual(forces_after_one, 1)
        # Taking nothing more must not increase the force count.
        self.assertEqual(self.solver.counter.forces, forces_after_one)
        self.assertTrue(self.solver.is_unevaluated(tail))

    def test_bounded_prefix_leaves_later_work_unforced(self):
        self.solver.counter.reset()
        stream = self.solver.open_stream(8)
        for _ in range(10):
            event, stream, finished = self.solver.next_event(stream)
            self.assertIsNotNone(event)
            self.assertFalse(finished)
        forces = self.solver.counter.forces
        self.assertTrue(self.solver.is_unevaluated(stream))
        # A second independent open still starts at zero search on that stream.
        other = self.solver.open_stream(8)
        self.assertTrue(self.solver.is_unevaluated(other))
        self.assertEqual(self.solver.counter.forces, forces)

    def test_safety_same_column_and_both_diagonals(self):
        # Row 0 col 0 placed; row 1 col 0 same column; col 1 diagonal.
        events, _ = self.take(4, limit=20)
        kinds = [event["event"] for event in events]
        self.assertEqual(kinds[:2], ["try", "place"])
        self.assertEqual(events[0], {"event": "try", "column": 0, "row": 0, "board": []})
        self.assertEqual(events[1], {"event": "place", "column": 0, "row": 0, "board": [0]})
        # After placing (0) in row 0, trying column 0 in row 1 is a same-column reject.
        reject_same = next(
            event for event in events
            if event["event"] == "reject" and event["row"] == 1 and event["column"] == 0
        )
        self.assertEqual(reject_same["board"], [0])
        reject_diag = next(
            event for event in events
            if event["event"] == "reject" and event["row"] == 1 and event["column"] == 1
        )
        self.assertEqual(reject_diag["board"], [0])
        # Column 2 in row 1 is safe after [0].
        place_safe = next(
            event for event in events
            if event["event"] == "place" and event["row"] == 1 and event["column"] == 2
        )
        self.assertEqual(place_safe["board"], [0, 2])

    def test_cps_resumes_at_the_next_candidate_after_reject_and_backtrack(self):
        events, _ = self.take(4, limit=40)
        # A reject is followed by the next try in the same row, higher column.
        for index, event in enumerate(events[:-1]):
            if event["event"] == "reject":
                following = events[index + 1]
                self.assertEqual(following["event"], "try")
                self.assertEqual(following["row"], event["row"])
                self.assertEqual(following["column"], event["column"] + 1)
                break
        else:
            self.fail("expected a reject followed by the next try")
        for index, event in enumerate(events[:-1]):
            if event["event"] == "backtrack":
                following = events[index + 1]
                self.assertEqual(following["event"], "try")
                self.assertEqual(following["row"], event["row"])
                self.assertEqual(following["column"], event["column"] + 1)
                self.assertEqual(following["board"], event["board"])
                break
        else:
            self.fail("expected a backtrack followed by the next try")

    def test_each_required_event_kind_appears(self):
        events, _ = self.take(4)
        names = {event["event"] for event in events}
        self.assertEqual(names, {"try", "place", "reject", "backtrack", "solution", "done"})
        self.assertEqual(events[-1], {"event": "done"})
        self.assertEqual(sum(1 for event in events if event["event"] == "done"), 1)

    def test_four_queens_solutions_are_exact_and_ordered(self):
        events, _ = self.take(4)
        solutions = [event["board"] for event in events if event["event"] == "solution"]
        self.assertEqual(solutions, FOUR_SOLUTIONS)
        self.assertEqual(len(solutions), len({tuple(board) for board in solutions}))

    def test_eight_queens_has_ninety_two_distinct_solutions(self):
        stream = self.solver.open_stream(8)
        solutions = []
        while True:
            event, stream, finished = self.solver.next_event(stream)
            if event is None:
                break
            if event["event"] == "solution":
                solutions.append(event["board"])
            if finished:
                self.assertEqual(event["event"], "done")
                break
        self.assertEqual(len(solutions), 92)
        self.assertEqual(len({tuple(board) for board in solutions}), 92)
        for board in solutions:
            self.assertEqual(len(board), 8)
            self.assertEqual(len(set(board)), 8)
            self._assert_safe(board)

    def _assert_safe(self, board):
        for row, column in enumerate(board):
            for earlier, other in enumerate(board[:row]):
                distance = row - earlier
                self.assertNotEqual(column, other)
                self.assertNotEqual(column, other - distance)
                self.assertNotEqual(column, other + distance)


if __name__ == "__main__":
    unittest.main()
