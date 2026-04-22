#!/usr/bin/env python3
"""TCP server for lab Mission A: bind, listen, accept; UTF-8 text lines."""

from __future__ import annotations

import argparse
import os
import socket
import sys


DEFAULT_PORT = 5000


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="TCP echo server (UTF-8, newline-delimited).")
    p.add_argument(
        "--host",
        default=os.environ.get("ZT_HOST", "0.0.0.0"),
        help="Bind address (lab: use your ZeroTier IP). Default: ZT_HOST env or 0.0.0.0.",
    )
    p.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", DEFAULT_PORT)),
        help=f"Listen port (default {DEFAULT_PORT} or PORT env).",
    )
    p.add_argument(
        "--backlog",
        type=int,
        default=5,
        help="listen() backlog.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.host in ("0.0.0.0", "::"):
        print(
            "Warning: binding to all interfaces. Lab text suggests binding to your ZeroTier IP; "
            "use --host <ZeroTier_IP> or set ZT_HOST.",
            file=sys.stderr,
        )

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((args.host, args.port))
        sock.listen(args.backlog)
        print(f"TCP listening on {args.host}:{args.port} (UTF-8 lines, Ctrl+C to stop)")
        while True:
            conn, addr = sock.accept()
            print(f"Accepted from {addr}")
            try:
                with conn:
                    r = conn.makefile("r", encoding="utf-8", newline="\n")
                    w = conn.makefile("w", encoding="utf-8", newline="\n")
                    try:
                        for line in r:
                            text = line.rstrip("\r\n")
                            print(f"  recv: {text!r}")
                            w.write(f"OK {text}\n")
                            w.flush()
                    except (UnicodeDecodeError, OSError) as e:
                        print(f"  I/O error: {e}", file=sys.stderr)
            except OSError as e:
                print(f"Connection error: {e}", file=sys.stderr)
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        sock.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
