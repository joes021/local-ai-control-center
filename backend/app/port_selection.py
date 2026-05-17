from __future__ import annotations

import socket
from collections.abc import Callable


def _default_is_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def select_first_free_port(
    start: int,
    end: int,
    is_port_available: Callable[[int], bool] | None = None,
) -> int:
    checker = is_port_available or _default_is_port_available
    for port in range(start, end + 1):
        if checker(port):
            return port
    raise RuntimeError(f"No free port available in range {start}-{end}")
