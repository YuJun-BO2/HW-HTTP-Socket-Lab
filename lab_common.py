"""Student-specific case generation. Python standard library only."""
import hashlib
import re
from urllib.parse import quote

ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,24}$")

def case_for(student_id):
    if not ID_PATTERN.fullmatch(student_id):
        raise ValueError("student_id must be 3-24 ASCII letters, digits, _ or -")
    h = hashlib.sha256(("kurose-ch2-lab-v1:" + student_id).encode("utf-8")).hexdigest()
    token = h[:8]
    prefix = f"/lab/{student_id}-{token}"
    hello = f"Hello, {student_id}! Token={token}\n"
    unicode_text = f"網路實驗：{student_id}｜測試成功\n"
    return {
        "student_id": student_id,
        "token": token,
        "prefix": prefix,
        "hello_path": prefix + "/hello",
        "unicode_path": prefix + "/unicode",
        "redirect_path": prefix + "/redirect",
        "missing_path": prefix + "/not-found",
        "echo_path": prefix + "/echo",
        "hello_body": hello,
        "unicode_body": unicode_text,
    }
