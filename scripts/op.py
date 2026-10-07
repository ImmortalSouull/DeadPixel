"""Sends messages over the Minecraft mod's link (ws://127.0.0.1:25599), no dependencies.

  python scripts/op.py test                 -> {"t":"gta","op":"test"} (relayed to the host mod)
  python scripts/op.py uimode 0             -> {"t":"gta","op":"uimode","v":0}
  python scripts/op.py --raw '{"t":"cmd","c":"time set noon"}'
Ops for the host: test [1: + far pillars], toggle, trace, uimode 0|1, uidraw n, lag 0..2, roll 0|1,
debug 0..3 (effect DebugView), dscale n (HostDepthScale x1000), near n (host near plane, mm).
"""
import base64
import json
import os
import socket
import struct
import sys
import time


def send(messages, port=25599):
    s = socket.create_connection(("127.0.0.1", port), timeout=3)
    key = base64.b64encode(os.urandom(16)).decode()
    s.sendall((f"GET / HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
               f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
    reply = b""
    while b"\r\n\r\n" not in reply:
        reply += s.recv(4096)
    if b" 101 " not in reply.split(b"\r\n")[0]:
        raise SystemExit(f"handshake failed: {reply[:80]!r}")
    # the mod greets every client ({"t":"hello"}); closing before that arrives drops the connection on its side
    rest = reply.split(b"\r\n\r\n", 1)[1]
    while b"hello" not in rest:
        rest += s.recv(4096)
    for text in messages:
        data = text.encode()
        mask = os.urandom(4)
        n = len(data)
        head = bytes([0x81]) + (bytes([0x80 | n]) if n < 126 else bytes([0x80 | 126]) + struct.pack(">H", n))
        s.sendall(head + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))
        print("sent", text)
    time.sleep(0.3)
    s.sendall(bytes([0x88, 0x80]) + os.urandom(4))
    s.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    if args[0] == "--raw":
        send(args[1:])
    else:
        msg = {"t": "gta", "op": args[0]}
        if len(args) > 1:
            msg["v"] = int(args[1])
        send([json.dumps(msg, separators=(",", ":"))])
