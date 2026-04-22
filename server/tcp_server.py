#!/usr/bin/env python3
"""TCP server: bind, listen, accept; bidirectional UTF-8 line chat + optional echo."""

from __future__ import annotations

import argparse
import os
import queue
import select
import socket
import sys
import threading


DEFAULT_PORT = 5000


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="TCP server (UTF-8 lines): receive from peer, send lines from stdin."
    )
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
    p.add_argument(
        "--no-echo",
        action="store_true",
        help="Do not send automatic 'OK <line>' replies; only stdin is sent to the client.",
    )
    return p.parse_args()


def _stdin_reader(q: "queue.Queue[str | None]", stop: threading.Event) -> None:
    try:
        while not stop.is_set():
            line = sys.stdin.readline()
            if line == "":
                q.put(None)
                return
            q.put(line)
    except OSError:
        q.put(None)


def _serve_one(conn: socket.socket, addr: tuple[str, int], echo: bool) -> None:
    print(f"Accepted from {addr}. Type lines to send to the client (UTF-8); Ctrl+C to stop.")
    if echo:
        print("(Echo ACKs: ON — use --no-echo to send only what you type.)")

    out_q: queue.Queue[str | None] = queue.Queue()
    stop = threading.Event()
    stdin_thread = threading.Thread(target=_stdin_reader, args=(out_q, stop), daemon=True)
    stdin_thread.start()

    buf = b""
    try:
        while True:
            try:
                r, _, _ = select.select([conn], [], [], 0.2)
            except (ValueError, OSError):
                break
            if r:
                chunk = conn.recv(4096)
                if not chunk:
                    print("Peer closed the connection (recv EOF).")
                    break
                buf += chunk
                while True:
                    idx = buf.find(b"\n")
                    if idx < 0:
                        break
                    raw_line, buf = buf[:idx], buf[idx + 1 :]
                    try:
                        text = raw_line.decode("utf-8")
                    except UnicodeDecodeError as e:
                        print(f"  UTF-8 decode error: {e}", file=sys.stderr)
                        continue
                    text = text.rstrip("\r")
                    print(f"peer> {text!r}")
                    if echo:
                        try:
                            conn.sendall(f"OK {text}\n".encode("utf-8"))
                        except OSError as e:
                            print(f"  send error: {e}", file=sys.stderr)
                            return

            while True:
                try:
                    item = out_q.get_nowait()
                except queue.Empty:
                    break
                if item is None:
                    print("stdin closed; stopping send loop.")
                    return
                line = item if item.endswith("\n") else item + "\n"
                try:
                    conn.sendall(line.encode("utf-8"))
                except OSError as e:
                    print(f"send error: {e}", file=sys.stderr)
                    return
    finally:
        stop.set()
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        conn.close()


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
            try:
                _serve_one(conn, addr, echo=not args.no_echo)
            except OSError as e:
                print(f"Connection error: {e}", file=sys.stderr)
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        sock.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
