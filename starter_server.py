"""Intentionally buggy HTTP/1.1 over TCP starter code: DO NOT treat as reference solution.

Student task: fix TCP stream reading, HTTP semantics, Content-Length,
Location, and robust sending while preserving the specified endpoints.
"""
import argparse
import socket
from urllib.parse import parse_qs, urlsplit
from lab_common import case_for


def handle_connection(conn, case):
    conn.settimeout(3)
    try:
        # BUG AREA A: TCP recv() does not correspond to a complete HTTP request.
        raw_request = conn.recv(1024)
        request_text = raw_request.decode("utf-8", errors="replace")
        request_line = request_text.split("\r\n", 1)[0]
        fields = request_line.split(" ")
        if len(fields) != 3:
            status, body_text = "400 Bad Request", "Bad Request\n"
            target = ""
        else:
            method, target, version = fields
            # BUG AREA B: ignores method and Host requirements.
            path = urlsplit(target).path
            if path == case["hello_path"]:
                status, body_text = "200 OK", case["hello_body"]
            elif path == case["unicode_path"]:
                status, body_text = "200 OK", case["unicode_body"]
            elif path == case["redirect_path"]:
                # BUG AREA C: redirect response should include Location.
                status, body_text = "302 Found", "Redirect\n"
            elif path == case["echo_path"]:
                msg = parse_qs(urlsplit(target).query).get("msg", [""])[0]
                status, body_text = "200 OK", f"ECHO: {msg}\n"
            else:
                status, body_text = "404 Not Found", "Not Found\n"

        # BUG AREA D: str length is not UTF-8 byte length.
        header = (
            f"HTTP/1.1 {status}\r\n"
            f"Content-Type: text/plain; charset=utf-8\r\n"
            f"Content-Length: {len(body_text)}\r\n"
            f"Connection: close\r\n\r\n"
        )
        response = header.encode("ascii") + body_text.encode("utf-8")
        # BUG AREA E: send() is not guaranteed to send the full byte sequence.
        conn.send(response)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"client error: {exc}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--student-id", required=True)
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    case = case_for(args.student_id)
    print(f"Starter server: http://127.0.0.1:{args.port}{case['hello_path']}", flush=True)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", args.port))
        server.listen(20)
        try:
            while True:
                conn, _ = server.accept()
                with conn:
                    handle_connection(conn, case)
        except KeyboardInterrupt:
            print("\nServer stopped")

if __name__ == "__main__":
    main()
