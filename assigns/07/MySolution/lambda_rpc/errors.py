"""JSON-RPC error codes and the exception that carries one to the dispatcher."""

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

LAMBDA_SYNTAX_ERROR = -32010
LAMBDA_TYPE_ERROR = -32011
EXECUTION_TIMEOUT = -32012
LAMBDA_RUNTIME_ERROR = -32013
RESULT_TOO_LARGE = -32014

MESSAGES = {
    PARSE_ERROR: "Parse error",
    INVALID_REQUEST: "Invalid Request",
    METHOD_NOT_FOUND: "Method not found",
    INVALID_PARAMS: "Invalid params",
    INTERNAL_ERROR: "Internal error",
    LAMBDA_SYNTAX_ERROR: "LAMBDA syntax error",
    LAMBDA_TYPE_ERROR: "LAMBDA type error",
    EXECUTION_TIMEOUT: "Execution timeout",
    LAMBDA_RUNTIME_ERROR: "LAMBDA runtime error",
    RESULT_TOO_LARGE: "Result too large",
}


class RpcError(Exception):
    """An error the client is meant to see. Anything else becomes -32603."""

    def __init__(self, code: int, data: dict | None = None):
        super().__init__(MESSAGES[code])
        self.code = code
        self.message = MESSAGES[code]
        self.data = data

    def to_object(self) -> dict:
        error = {"code": self.code, "message": self.message}
        if self.data is not None:
            error["data"] = self.data
        return error


def invalid_params(param: str | None, reason: str, **extra) -> RpcError:
    return RpcError(INVALID_PARAMS, {"param": param, "reason": reason, **extra})
