"""Flask transport: POST /rpc for JSON-RPC, static files for the animation."""

from __future__ import annotations

import json
from pathlib import Path

from flask import Flask, Response, request, send_from_directory
from werkzeug.exceptions import HTTPException

from .config import Limits
from .jsonrpc import Dispatcher
from .service import QueensService

STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
JSON_CHARSETS = {"utf-8", "utf8"}


def create_app(service: QueensService | None = None, limits: Limits | None = None) -> Flask:
    limits = limits or Limits()
    service = service or QueensService(limits=limits)
    dispatcher = Dispatcher(service.methods())

    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = limits.max_body_bytes
    app.extensions["queens_rpc.service"] = service
    app.extensions["queens_rpc.dispatcher"] = dispatcher

    @app.get("/")
    def index():
        return send_from_directory(STATIC_DIR, "index.html")

    @app.get("/static/<path:name>")
    def static_file(name: str):
        return send_from_directory(STATIC_DIR, name)

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
