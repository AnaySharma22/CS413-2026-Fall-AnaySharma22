"""Applied source and operation state. No HTTP, HTML, or language evaluation."""

MAX_BYTES = 65536
SOURCE_OPERATIONS = ("lint", "interpret", "typecheck", "compile")


class Model:
    def __init__(self):
        self.name = ""
        self.source = ""
        self.revision = 0
        self.result = None
        self.artifact = None
        self.busy = False

    def apply(self, source, name):
        if self.busy:
            raise ValueError("An operation is in progress.")
        if not isinstance(source, str) or not source.strip():
            raise ValueError("Source cannot be empty or whitespace.")
        if len(source.encode("utf-8")) > MAX_BYTES:
            raise ValueError("Source exceeds the 65,536-byte limit.")
        self.source = source
        self.name = str(name or "Untitled")[:200]
        self.revision += 1
        self.result = None
        self.artifact = None

    def begin(self, operation):
        if self.busy:
            raise ValueError("An operation is already in progress.")
        if operation == "execute":
            raise ValueError(
                "Execute is for generated code and is unavailable until "
                "compilation is implemented and produces an artifact."
            )
        if operation not in SOURCE_OPERATIONS:
            raise ValueError("Unknown operation.")
        if self.revision == 0:
            raise ValueError("Apply source before running tools.")
        if operation == "compile":
            self.artifact = None
        self.busy = True

    def finish(self, operation, result):
        self.result = {
            "operation": operation,
            "revision": self.revision,
            "outcome": result["outcome"],
            "text": result["text"],
        }
        self.busy = False
