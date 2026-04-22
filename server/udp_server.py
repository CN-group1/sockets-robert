#!/usr/bin/env python3
"""UDP server for lab Mission B: receive numbered UTF-8 datagrams; report gaps."""

from __future__ import annotations

import argparse
import os
import re
import socket
import sys
import time
from typing import Optional

DEFAULT_PORT = 5001
_SEQ_RE = re.compile(r"^(?:MSG\s*)?(\d+)\b", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="UDP server: numbered messages, UTF-8.")
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
        "--expect",
        type=int,
        default=100,
        help="Expected distinct sequence numbers 1..N (default 100).",
    )
    p.add_argument(
        "--idle-timeout",
        type=float,
        default=5.0,
        help="Seconds without a datagram before printing a progress summary (default 5).",
    )
    return p.parse_args()


def extract_seq(payload: str) -> Optional[int]:
    payload = payload.strip()
    if not payload:
        return None
    m = _SEQ_RE.match(payload)
    if m:
        return int(m.group(1))
    try:
        return int(payload)
    except ValueError:
        return None


def print_summary(
    seen: set[int],
    expect: int,
    dupes: int,
    bad: int,
    last_peer: Optional[tuple[str, int]],
) -> None:
    exp_set = set(range(1, expect + 1))
    missing = sorted(exp_set - seen)
    print(
        f"Summary: unique_ok={len(seen)}/{expect}, dupes={dupes}, "
        f"unparseable={bad}, missing={len(missing)} {missing[:20]}{'...' if len(missing) > 20 else ''}"
    )
    if last_peer:
        print(f"Last peer: {last_peer[0]}:{last_peer[1]}")


def main() -> int:
    args = parse_args()
    if args.host in ("0.0.0.0", "::"):
        print(
            "Warning: binding to all interfaces. Lab suggests your ZeroTier IP; "
            "use --host <ZeroTier_IP> or set ZT_HOST.",
            file=sys.stderr,
        )

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((args.host, args.port))
    sock.settimeout(1.0)
    print(
        f"UDP listening on {args.host}:{args.port} "
        f"(expect ids 1..{args.expect}, UTF-8; Ctrl+C to stop)"
    )

    seen: set[int] = set()
    dupes = 0
    bad = 0
    last_peer: Optional[tuple[str, int]] = None
    last_rx = time.monotonic()

    try:
        while True:
            try:
                data, addr = sock.recvfrom(2048)
            except socket.timeout:
                if seen and (time.monotonic() - last_rx) >= args.idle_timeout:
                    print("(idle timeout)")
                    print_summary(seen, args.expect, dupes, bad, last_peer)
                    last_rx = time.monotonic()
                continue

            last_rx = time.monotonic()
            last_peer = addr
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                bad += 1
                print(f"Non-UTF-8 datagram from {addr}, len={len(data)}")
                continue

            seq = extract_seq(text)
            if seq is None:
                bad += 1
                print(f"Unparseable from {addr}: {text!r}")
                continue

            if 1 <= seq <= args.expect:
                if seq in seen:
                    dupes += 1
                else:
                    seen.add(seq)
                    if len(seen) % 10 == 0 or len(seen) == args.expect:
                        print(f"Progress: {len(seen)}/{args.expect} unique")
                if len(seen) == args.expect:
                    print("All expected sequence numbers received.")
                    print_summary(seen, args.expect, dupes, bad, last_peer)
                    break
            else:
                bad += 1
                print(f"Out-of-range id {seq} from {addr} (expected 1..{args.expect})")

    except KeyboardInterrupt:
        print("\nShutting down.")
        print_summary(seen, args.expect, dupes, bad, last_peer)
    finally:
        sock.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
