"""Model and controller tests. No browser and no web server."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend import Backend
from controller import Controller
from model import Model


class ModelTests(unittest.TestCase):
    def test_manual_input_replacement_and_rejection(self):
        model = Model()
        model.apply("D0Eint(1)", "Manual input")
        self.assertEqual(model.revision, 1)
        self.assertEqual(model.name, "Manual input")
        for source in ("", "  \n", "x" * 65537):
            with self.assertRaises(ValueError):
                model.apply(source, "Bad")
            self.assertEqual(model.source, "D0Eint(1)")
            self.assertEqual(model.revision, 1)
        model.result = {"text": "old"}
        model.artifact = {"format": "none"}
        model.apply("D0Eint(2)", "Replacement")
        self.assertEqual(model.revision, 2)
        self.assertEqual(model.source, "D0Eint(2)")
        self.assertIsNone(model.result)
        self.assertIsNone(model.artifact)

    def test_exact_size_limit(self):
        model = Model()
        body = "D0Eint(1)" + (" " * (65536 - len("D0Eint(1)")))
        self.assertEqual(len(body.encode("utf-8")), 65536)
        model.apply(body, "Edge")
        with self.assertRaises(ValueError):
            model.apply(body + " ", "Edge")
        self.assertEqual(model.source, body)


class ControllerTests(unittest.TestCase):
    def test_unapplied_edit_blocks_tools_and_keeps_source(self):
        controller = Controller(Backend(bounded=False))
        controller.apply("D0Eint(1)", "Manual input")
        with self.assertRaises(ValueError):
            controller.run("lint", "D0Eint(1)\n")
        self.assertEqual(controller.state()["source"], "D0Eint(1)")
        self.assertIsNone(controller.state()["result"])

    def test_placeholders_and_execute_do_not_succeed(self):
        class Exploding:
            def run(self, operation, source):
                raise AssertionError("execute must not call the backend")

        controller = Controller(Exploding())
        with self.assertRaises(ValueError):
            controller.run("execute", "")
        controller = Controller(Backend(bounded=False))
        controller.apply("D0Eint(1)", "Manual input")
        for operation in ("typecheck", "compile"):
            state = controller.run(operation, "D0Eint(1)")
            self.assertEqual(state["result"]["outcome"], "not_implemented")
            self.assertEqual(state["result"]["revision"], 1)
            self.assertEqual(state["result"]["operation"], operation)
        self.assertIsNone(controller.state()["artifact"])
        self.assertFalse(controller.state()["execute_available"])
        with self.assertRaises(ValueError):
            controller.run("execute", "D0Eint(1)")
        self.assertIsNone(controller.state()["artifact"])

    def test_busy_failure_and_retry(self):
        holder = {}

        class Fake:
            def __init__(self):
                self.fail = True
                self.calls = []

            def run(self, operation, source):
                self.calls.append((operation, source))
                with self_test.assertRaises(ValueError):
                    holder["controller"].apply("D0Eint(4)", "Busy")
                with self_test.assertRaises(ValueError):
                    holder["controller"].run("lint", source)
                if self.fail:
                    raise OSError("worker down")
                return {"outcome": "success", "text": "retried"}

        self_test = self
        fake = Fake()
        controller = Controller(fake)
        holder["controller"] = controller
        with self.assertRaises(ValueError):
            controller.run("lint", "")
        controller.apply("D0Eint(3)", "Manual input")
        failed = controller.run("interpret", "D0Eint(3)")
        self.assertEqual(failed["result"]["outcome"], "backend_error")
        self.assertFalse(failed["busy"])
        self.assertEqual(failed["source"], "D0Eint(3)")
        fake.fail = False
        retried = controller.run("lint", "D0Eint(3)")
        self.assertEqual(retried["result"]["outcome"], "success")
        self.assertEqual(retried["result"]["text"], "retried")
        self.assertEqual(fake.calls[-1], ("lint", "D0Eint(3)"))


if __name__ == "__main__":
    unittest.main()
