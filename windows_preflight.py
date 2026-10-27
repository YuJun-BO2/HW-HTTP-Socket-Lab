"""Optional preflight for Windows 10/11 students. Standard library only.

This script cannot automatically certify Npcap capture permissions; verify in Wireshark.
"""
import argparse
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import sys


def locate_wireshark():
    candidates = [shutil.which("Wireshark.exe"), shutil.which("wireshark")]
    for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
        if base:
            candidates.append(str(Path(base) / "Wireshark" / "Wireshark.exe"))
    return next((candidate for candidate in candidates if candidate and Path(candidate).is_file()), None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    print("Kurose Ch2 Windows environment check")
    print("Operating system:", platform.platform())
    print("Python:", sys.version.split()[0], "-", sys.executable)
    good_python = sys.version_info >= (3, 10)
    print("Python 3.10+:", "PASS" if good_python else "FAIL")
    exe = shutil.which("curl.exe") if os.name == "nt" else shutil.which("curl")
    print("curl.exe / curl:", exe or "NOT FOUND")
    if exe:
        result = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=6)
        print("curl command:", "PASS" if result.returncode == 0 else "FAIL")
    else:
        print("curl command: NOT FOUND")
    if os.name == "nt":
        wireshark = locate_wireshark()
        print("Wireshark.exe:", wireshark or "NOT FOUND in common locations")
        print("Npcap: inspect Wireshark capture interfaces manually")
        print("Expected interface: Adapter for loopback traffic capture")
    else:
        print("This check also runs outside Windows; Windows capture must be tested separately.")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", args.port))
        print(f"Loopback port {args.port}: available")
    except OSError as exc:
        print(f"Loopback port {args.port}: in use or unavailable ({exc})")
        print("Tip: stop the earlier server or pick another port in both terminal commands.")
    print("Network access: not required. Bind server only to 127.0.0.1.")
    print("Run Wireshark on the same Windows host, not inside WSL or a different VM.")
    return 0 if good_python and exe else 1

if __name__ == "__main__":
    raise SystemExit(main())
