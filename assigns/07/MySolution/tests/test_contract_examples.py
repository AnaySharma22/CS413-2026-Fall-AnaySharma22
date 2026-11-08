"""RPC.md section 7 is executable: replay every example and compare exactly."""

from __future__ import annotations

import json
import re
import unittest

from support import REQUEST_BODY, SOLUTION_DIR, Client, build_app

GENERATED = "<generated code>"
HTTP_BLOCK = re.compile(r"```http\n(.*?)```", re.DOTALL)


def load_examples():
    text = (SOLUTION_DIR / "RPC.md").read_text("utf-8")
    section = text.split("## 7. Examples", 1)[1].split("\n## ", 1)[0]
    blocks = HTTP_BLOCK.findall(section)
    if len(blocks) % 2:
        raise ValueError("RPC.md examples must come in request/response pairs")
    examples = []
    for request, response in zip(blocks[0::2], blocks[1::2]):
        request_head, _, request_body = request.partition("\n\n")
        response_head, _, response_body = response.partition("\n\n")
        examples.append({
            "request_line": request_head.splitlines()[0],
            "body": request_body.strip().encode("utf-8"),
            "status": int(response_head.splitlines()[0].split()[1]),
            "response": response_body.strip(),
        })
    return examples


def with_generated_code(expected, actual):
    """Replace the documented placeholder with the real code after checking it."""
    if isinstance(expected, dict) and isinstance(actual, dict):
        return {key: with_generated_code(value, actual.get(key)) for key, value in expected.items()}
    if isinstance(expected, list) and isinstance(actual, list) and len(expected) == len(actual):
        return [with_generated_code(e, a) for e, a in zip(expected, actual)]
    if expected == GENERATED and isinstance(actual, str) and actual.strip():
        return actual
    return expected


class ContractExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = Client(build_app())
        cls.examples = load_examples()

    def test_every_documented_example_matches_the_service(self):
        self.assertGreaterEqual(len(self.examples), 12)
        for number, example in enumerate(self.examples, 1):
            with self.subTest(example=number, body=example["body"][:80]):
                self.assertEqual(example["request_line"], "POST /rpc HTTP/1.1")
                response = self.client.post(raw=example["body"])
                self.assertEqual(response.status_code, example["status"])
                if example["status"] == 204:
                    self.assertEqual(response.get_data(), b"")
                    continue
                actual = response.get_json()
                expected = with_generated_code(json.loads(example["response"]), actual)
                self.assertEqual(actual, expected)

    def test_well_formed_example_requests_match_the_schema(self):
        accepted = 0
        for example in self.examples:
            try:
                payload = json.loads(example["body"])
            except ValueError:
                continue
            if REQUEST_BODY.is_valid(payload):
                accepted += 1
        self.assertGreaterEqual(accepted, 8)

    def test_schema_rejects_what_the_service_rejects(self):
        rejected = [
            {"jsonrpc": "1.0", "method": "service.health", "id": 1},
            {"jsonrpc": "2.0", "method": "service.health", "id": True},
            {"jsonrpc": "2.0", "method": "service.health", "id": 1, "extra": 1},
            {"jsonrpc": "2.0", "method": "lambda.typecheck", "params": {"source": "  "}, "id": 1},
            {"jsonrpc": "2.0", "method": "lambda.compile", "params": {"source": "1"}, "id": 1},
            {"jsonrpc": "2.0", "method": "lambda.compile",
             "params": {"source": "1", "target": "ruby"}, "id": 1},
            {"jsonrpc": "2.0", "method": "lambda.interpret",
             "params": {"source": "1", "libraries": ["nope"]}, "id": 1},
            [],
        ]
        for payload in rejected:
            with self.subTest(payload=payload):
                self.assertFalse(REQUEST_BODY.is_valid(payload))


if __name__ == "__main__":
    unittest.main()
