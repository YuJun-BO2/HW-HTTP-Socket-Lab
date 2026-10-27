"""Generate individualized manifest and raw HTTP examples for the student."""
import argparse
import json
from pathlib import Path
from urllib.parse import quote
from lab_common import case_for


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--student-id", required=True)
    p.add_argument("--out", default="my_case.json")
    a = p.parse_args()
    c = case_for(a.student_id)
    c["unicode_utf8_bytes"] = len(c["unicode_body"].encode("utf-8"))
    c["hello_utf8_bytes"] = len(c["hello_body"].encode("utf-8"))
    c["example_message"] = "台北 TCP / HTTP"
    c["example_echo_target"] = c["echo_path"] + "?msg=" + quote(c["example_message"], safe="")
    c["raw_get_request"] = f"GET {c['hello_path']} HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n"
    Path(a.out).write_text(json.dumps(c, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Generated {a.out}; token={c['token']} ; UTF-8 bytes={c['unicode_utf8_bytes']}")

if __name__ == "__main__":
    main()
