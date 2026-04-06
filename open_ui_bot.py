#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time
import urllib.error
import urllib.request
import webbrowser


def wait_for_url(url: str, timeout: int, interval: float) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if 200 <= response.status < 500:
                    return True
        except (urllib.error.URLError, TimeoutError):
            time.sleep(interval)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Waits for the web interface and opens it in your default browser.",
    )
    parser.add_argument(
        "--url",
        default="http://localhost:3000",
        help="Frontend URL to open. Default: http://localhost:3000",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="How many seconds to wait for the site. Default: 120",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="How often to retry in seconds. Default: 2.0",
    )
    args = parser.parse_args()

    print(f"Waiting for web UI: {args.url}")
    is_ready = wait_for_url(args.url, timeout=args.timeout, interval=args.interval)
    if not is_ready:
        print(f"Web UI did not become available within {args.timeout} seconds.", file=sys.stderr)
        return 1

    opened = webbrowser.open(args.url, new=2)
    if opened:
        print(f"Opened browser: {args.url}")
    else:
        print(f"Site is ready, but automatic browser launch failed. Open manually: {args.url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
