"""Start the LAMBDA3 JSON-RPC service: python MySolution/serve.py (from assigns/07)."""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> None:
    from lambda_rpc import Limits, create_app

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--time-limit",
        type=float,
        default=Limits.time_limit_seconds,
        help="seconds allowed for each source call (default %(default)s)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    app = create_app(limits=Limits(time_limit_seconds=args.time_limit))
    print(f"LAMBDA3 JSON-RPC service on http://{args.host}:{args.port}/rpc")
    app.run(host=args.host, port=args.port, threaded=True, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
