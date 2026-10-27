"""Public, reproducible functional tests for a running lab HTTP server."""
import argparse
from pathlib import Path
from urllib.parse import quote
from lab_common import case_for
from socket_testkit import exchange, request, parse_response, split_request_while_asserting_no_early_response


def cases(c, port):
    def basic_200():
        status, headers, body = parse_response(exchange(port, request("GET", c["hello_path"])))
        assert status == 200
        assert body.decode("utf-8") == c["hello_body"]
        assert headers.get("content-type") == "text/plain; charset=utf-8"

    def not_found():
        status, _, body = parse_response(exchange(port, request("GET", c["missing_path"])))
        assert status == 404 and body == b"Not Found\n"

    def utf8_length():
        status, _, body = parse_response(exchange(port, request("GET", c["unicode_path"])))
        assert status == 200 and body.decode("utf-8") == c["unicode_body"]

    def redirect():
        status, headers, body = parse_response(exchange(port, request("GET", c["redirect_path"])))
        assert status == 302 and headers.get("location") == c["hello_path"]
        assert body == b"Redirect\n"

    def wrong_method():
        status, headers, body = parse_response(exchange(port, request("POST", c["hello_path"])))
        assert status == 405 and headers.get("allow") == "GET"
        assert body == b"Method Not Allowed\n"

    def missing_host():
        status, _, body = parse_response(exchange(port, request("GET", c["hello_path"], host=False)))
        assert status == 400 and body == b"Bad Request\n"

    def echo_query():
        msg = "HTTP 測試 42"
        path = c["echo_path"] + "?msg=" + quote(msg, safe="")
        status, _, body = parse_response(exchange(port, request("GET", path)))
        assert status == 200 and body.decode("utf-8") == f"ECHO: {msg}\n"

    def split_header():
        raw = request("GET", c["hello_path"])
        first, rest = raw.split(b"Host:", 1)
        response = split_request_while_asserting_no_early_response(port, first + b"Ho", b"st:" + rest)
        status, _, body = parse_response(response)
        assert status == 200 and body.decode("utf-8") == c["hello_body"]

    return [
        ("P01 normal GET 200", basic_200),
        ("P02 unknown path 404", not_found),
        ("P03 UTF-8 Content-Length", utf8_length),
        ("P04 302 requires Location", redirect),
        ("P05 POST gives 405", wrong_method),
        ("P06 HTTP/1.1 needs Host", missing_host),
        ("P07 percent-encoded UTF-8 echo", echo_query),
        ("P08 wait for all headers", split_header),
    ]


def run(student_id, port, log_path=None):
    c = case_for(student_id)
    passed = 0
    messages = []

    def emit(message):
        print(message)
        messages.append(message)
    for name, fn in cases(c, port):
        try:
            fn()
            emit(f"PASS {name}")
            passed += 1
        except Exception as exc:
            emit(f"FAIL {name} -> {type(exc).__name__}: {exc}")
    emit(f"Result: {passed}/8 public tests passed")
    if log_path:
        Path(log_path).write_text("\n".join(messages) + "\n", encoding="utf-8")
        print(f"Saved UTF-8 log: {log_path}")
    return passed == 8

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--student-id", required=True)
    p.add_argument("--port", type=int, default=8080)
    p.add_argument("--log", help="Write results as UTF-8 text (recommended on Windows)")
    a = p.parse_args()
    raise SystemExit(0 if run(a.student_id, a.port, a.log) else 1)
