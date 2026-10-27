"""Minimal raw TCP/HTTP test helpers. No third-party packages."""
import socket
import time


def exchange(port, data, timeout=3.0):
    with socket.create_connection(("127.0.0.1", port), timeout=timeout) as conn:
        conn.settimeout(timeout)
        conn.sendall(data)
        chunks = []
        while True:
            part = conn.recv(8192)
            if not part:
                break
            chunks.append(part)
        return b"".join(chunks)


def request(method, path, *, host=True, other_headers="", body=b""):
    h = f"{method} {path} HTTP/1.1\r\n"
    if host:
        h += "Host: 127.0.0.1\r\n"
    h += "Connection: close\r\n" + other_headers + "\r\n"
    return h.encode("ascii") + body


def parse_response(raw):
    head, sep, body = raw.partition(b"\r\n\r\n")
    assert sep, "HTTP response is missing CRLF-CRLF header terminator"
    lines = head.decode("iso-8859-1").split("\r\n")
    assert lines[0].startswith("HTTP/1.1 "), f"Bad status line: {lines[0]!r}"
    code = int(lines[0].split(" ", 2)[1])
    headers = {}
    for line in lines[1:]:
        assert ":" in line, f"Malformed header: {line!r}"
        key, value = line.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    assert "content-length" in headers, "Content-Length is required for this lab"
    length = int(headers["content-length"])
    assert length == len(body), f"Content-Length={length}, actual bytes={len(body)}"
    assert headers.get("connection", "").lower() == "close", "Require Connection: close"
    return code, headers, body


def split_request_while_asserting_no_early_response(port, first_chunk, rest, pause=0.18):
    """Checks application completeness, not the number of TCP packets."""
    with socket.create_connection(("127.0.0.1", port), timeout=3) as conn:
        conn.sendall(first_chunk)
        conn.settimeout(pause)
        try:
            early = conn.recv(1)
            if early:
                raise AssertionError("Server responded before receiving complete CRLF-CRLF")
            raise AssertionError("Server closed connection before complete request")
        except socket.timeout:
            pass
        conn.settimeout(3)
        conn.sendall(rest)
        chunks = []
        while True:
            part = conn.recv(8192)
            if not part:
                break
            chunks.append(part)
        return b"".join(chunks)
