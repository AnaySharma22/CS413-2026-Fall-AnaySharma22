"""Flask transport: one endpoint, POST /rpc, carrying JSON-RPC 2.0 bodies.

HTTP status reports what happened to the HTTP request. Any JSON-RPC answer,
error or not, is sent with 200; 204 means there is nothing to send back.
Transport failures (wrong media type, oversized body, wrong method or path)
use 4xx statuses with short plain-text bodies.
"""

from __future__ import annotations

import json

from flask import Flask, Response, request
from werkzeug.exceptions import HTTPException

from .config import Limits
from .jsonrpc import Dispatcher
from .service import LambdaService

JSON_CHARSETS = {"utf-8", "utf8"}


def create_app(service: LambdaService | None = None, limits: Limits | None = None) -> Flask:
    limits = limits or (service.limits if service else Limits())
    service = service or LambdaService(limits=limits)
    dispatcher = Dispatcher(service.methods(), limits)

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = limits.max_body_bytes
    app.extensions["lambda_rpc.dispatcher"] = dispatcher

    @app.post("/rpc")
    def rpc() -> Response:
        charset = request.mimetype_params.get("charset", "utf-8").lower()
        if request.mimetype != "application/json" or charset not in JSON_CHARSETS:
            return _plain(415, "POST /rpc requires Content-Type: application/json")
        answer = dispatcher.handle_body(request.get_data(cache=False))
        if answer is None:
            return Response(status=204)
        return Response(json.dumps(answer), status=200, mimetype="application/json")

    @app.errorhandler(HTTPException)
    def transport_error(error: HTTPException) -> Response:
        response = _plain(error.code or 500, error.name)
        if error.code == 405:
            response.headers["Allow"] = "POST"
        return response

    return app


def _plain(status: int, text: str) -> Response:
    return Response(text + "\n", status=status, mimetype="text/plain")
