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
        # FIXED (P08)：持續累積到標頭結束；提前斷線或超過 8192 bytes 就結束處理。
        raw_request = b""
        while b"\r\n\r\n" not in raw_request:
            chunk = conn.recv(1024)
            if not chunk:
                return
            raw_request += chunk
            header_end = raw_request.find(b"\r\n\r\n")
            if (header_end + 4 if header_end >= 0 else len(raw_request)) > 8192:
                return
        request_text = raw_request.split(b"\r\n\r\n", 1)[0].decode("utf-8", errors="replace")
        request_line = request_text.split("\r\n", 1)[0]
        fields = request_line.split(" ")
        # FIXED (P04、P05)：各分支可加入額外標頭；格式錯誤時也保留空字串供回應使用。
        extra_headers = ""
        if len(fields) != 3 or not all(fields):
            status, body_text = "400 Bad Request", "Bad Request\n"
            target = ""
        else:
            method, target, version = fields
            # BUG AREA B: ignores method and Host requirements.
            path = urlsplit(target).path
            # FIXED (P06)：標頭名稱不分大小寫，Host 必須唯一且非空，格式錯誤回 400。
            headers = [line.partition(":") for line in request_text.split("\r\n")[1:]]
            hosts = [value.strip() for name, sep, value in headers if name.lower() == "host" and sep]
            bad_headers = any(not sep or not name or any(c.isspace() for c in name) for name, sep, _ in headers)
            if version != "HTTP/1.1" or bad_headers or len(hosts) != 1 or not hosts[0]:
                status, body_text = "400 Bad Request", "Bad Request\n"
            # FIXED (P05)：先拒絕非 GET 方法，附上 Allow，避免被後續路徑判斷覆蓋。
            elif method != "GET":
                status, body_text = "405 Method Not Allowed", "Method Not Allowed\n"
                extra_headers = "Allow: GET\r\n"
            elif path == case["hello_path"]:
                status, body_text = "200 OK", case["hello_body"]
            elif path == case["unicode_path"]:
                status, body_text = "200 OK", case["unicode_body"]
            elif path == case["redirect_path"]:
                # BUG AREA C: redirect response should include Location.
                status, body_text = "302 Found", "Redirect\n"
                # FIXED (P04)：讓用戶端知道重新導向的目的地。
                extra_headers = f"Location: {case['hello_path']}\r\n"
            elif path == case["echo_path"]:
                msg = parse_qs(urlsplit(target).query).get("msg", [""])[0]
                status, body_text = "200 OK", f"ECHO: {msg}\n"
            else:
                status, body_text = "404 Not Found", "Not Found\n"

        # BUG AREA D: str length is not UTF-8 byte length.
        # FIXED (P03、P07)：以 UTF-8 bytes 計算長度並傳送。
        body_bytes = body_text.encode("utf-8")
        header = (
            f"HTTP/1.1 {status}\r\n"
            f"Content-Type: text/plain; charset=utf-8\r\n"
            f"Content-Length: {len(body_bytes)}\r\n"
            # FIXED (P04、P05)：額外標頭要放在結束標頭的空行之前。
            f"Connection: close\r\n"
            f"{extra_headers}\r\n"
        )
        response = header.encode("ascii") + body_bytes
        # BUG AREA E: send() is not guaranteed to send the full byte sequence.
        # FIXED (E)：sendall() 會持續傳送直到完成或發生錯誤。
        conn.sendall(response)
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
