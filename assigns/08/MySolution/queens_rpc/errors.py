"""JSON-RPC error codes and a small exception type."""

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
UNKNOWN_STREAM = -32020

MESSAGES = {
    PARSE_ERROR: "Parse error",
    INVALID_REQUEST: "Invalid Request",
    METHOD_NOT_FOUND: "Method not found",
    INVALID_PARAMS: "Invalid params",
    INTERNAL_ERROR: "Internal error",
    UNKNOWN_STREAM: "Unknown stream",
}


class RpcError(Exception):
    def __init__(self, code: int, data=None):
        self.code = code
        self.data = data
        super().__init__(MESSAGES[code])

    def to_object(self) -> dict:
        error = {"code": self.code, "message": MESSAGES[self.code]}
        if self.data is not None:
            error["data"] = self.data
        return error


def invalid_params(param, reason, **extra):
    return RpcError(INVALID_PARAMS, {"param": param, "reason": reason, **extra})
