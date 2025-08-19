#!/usr/bin/env python3
"""
SHADOW-DNS: Termux Localhost → Public URL Tool (Python)

Features
- Serves any local folder over HTTP (uses Python's built‑in http.server)
- Exposes it to the internet via either Cloudflared (trycloudflare.com) or localhost.run over SSH
- Auto‑detects available tunnel method; prefers cloudflared if installed
- Prints the public URL when ready and keeps the tunnel alive (with colored output)

Usage examples
  python SHADOW-DNS.py              # serve current folder on port 8000 and get a public URL
  python SHADOW-DNS.py -p 9000 -d /sdcard/Download
  python SHADOW-DNS.py --no-public   # serve locally only

Prereqs (Termux)
  pkg update && pkg upgrade -y
  pkg install python openssh -y

optional but recommended for faster/cleaner tunnels:
  pkg install cloudflared -y

Notes
- Cloudflared is preferred when available; it usually gives an https://*.trycloudflare.com URL.
- SSH fallback uses localhost.run; it produces an http(s) URL in stdout.
- Press Ctrl+C to stop both the server and the tunnel.
"""

import argparse
import contextlib
import http.server
import os
import re
import shutil
import signal
import socket
import socketserver
import subprocess
import sys
import threading
import time
from typing import Optional

# ----------------------------- Colors -----------------------------
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"

# ----------------------------- Helpers -----------------------------

def which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)

class StoppableHTTPServer(socketserver.TCPServer):
    allow_reuse_address = True

    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        socketserver.TCPServer.server_bind(self)

# ----------------------- HTTP server launcher ----------------------

def start_http_server(port: int, directory: str) -> StoppableHTTPServer:
    handler = http.server.SimpleHTTPRequestHandler
    os.chdir(directory)
    httpd = StoppableHTTPServer(("0.0.0.0", port), handler)

    def _serve():
        try:
            print(f"{GREEN}[HTTP]{RESET} Serving '{directory}' on http://127.0.0.1:{port} (and 0.0.0.0:{port})")
            httpd.serve_forever(poll_interval=0.5)
        except KeyboardInterrupt:
            pass
        finally:
            with contextlib.suppress(Exception):
                httpd.server_close()

    t = threading.Thread(target=_serve, daemon=True)
    t.start()
    return httpd

# --------------------------- Tunnel logic --------------------------

URL_REGEX = re.compile(r"https?://[\w\-\.]+(?:/\S*)?")

class TunnelProcess:
    def __init__(self, proc: subprocess.Popen, name: str):
        self.proc = proc
        self.name = name
        self.url: Optional[str] = None

    def terminate(self):
        if self.proc and self.proc.poll() is None:
            with contextlib.suppress(Exception):
                self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                with contextlib.suppress(Exception):
                    self.proc.kill()

# --------------------------- Cloudflared ----------------------------

def start_cloudflared(port: int) -> Optional[TunnelProcess]:
    if not which("cloudflared"):
        return None
    cmd = ["cloudflared", "tunnel", "--url", f"http://localhost:{port}", "--no-autoupdate", "--metrics", ""]
    print(f"{YELLOW}[TUNNEL]{RESET} Starting Cloudflared…")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
    tp = TunnelProcess(proc, "cloudflared")

    def _reader():
        for line in proc.stdout:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            print(f"{BLUE}[cloudflared]{RESET} {line_stripped}")
            if not tp.url:
                m = URL_REGEX.search(line_stripped)
                if m and ("trycloudflare.com" in m.group(0) or ".cfargotunnel.com" in m.group(0)):
                    tp.url = m.group(0)
                    print(f"{GREEN}[PUBLIC]{RESET} {tp.url}")

    threading.Thread(target=_reader, daemon=True).start()
    return tp

# ------------------------- localhost.run SSH ------------------------

def start_localhost_run(port: int) -> Optional[TunnelProcess]:
    if not which("ssh"):
        print(f"{RED}[TUNNEL]{RESET} SSH not found; cannot use localhost.run fallback.")
        return None
    cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ServerAliveInterval=60", "-o", "ExitOnForwardFailure=yes", "-R", f"80:localhost:{port}", "nokey@localhost.run"]
    print(f"{YELLOW}[TUNNEL]{RESET} Starting localhost.run (SSH)…")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
    tp = TunnelProcess(proc, "localhost.run")

    def _reader():
        for line in proc.stdout:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            print(f"{BLUE}[localhost.run]{RESET} {line_stripped}")
            if not tp.url:
                m = URL_REGEX.search(line_stripped)
                if m:
                    tp.url = m.group(0)
                    print(f"{GREEN}[PUBLIC]{RESET} {tp.url}")

    threading.Thread(target=_reader, daemon=True).start()
    return tp

# ------------------------------ Main ------------------------------

def pick_free_port(preferred: int) -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        try:
            s.bind(("0.0.0.0", preferred))
            return preferred
        except OSError:
            pass
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("0.0.0.0", 0))
        return s.getsockname()[1]


def main():
    parser = argparse.ArgumentParser(description="Serve a directory locally and expose it with a public URL (Termux‑friendly)")
    parser.add_argument("-d", "--directory", default=os.getcwd(), help="Folder to serve (default: current directory)")
    parser.add_argument("-p", "--port", type=int, default=8000, help="Local port (default: 8000)")
    parser.add_argument("--no-public", action="store_true", help="Do not create a public tunnel; local only")
    args = parser.parse_args()

    directory = os.path.abspath(args.directory)
    if not os.path.isdir(directory):
        print(f"{RED}[ERR]{RESET} Directory not found: {directory}")
        sys.exit(1)

    port = pick_free_port(args.port)
    if port != args.port:
        print(f"{YELLOW}[INFO]{RESET} Port {args.port} busy, using {port} instead.")

    httpd = start_http_server(port, directory)

    tunnel: Optional[TunnelProcess] = None

    def cleanup(*_):
        print(f"\n{RED}[STOP]{RESET} Shutting down…")
        if tunnel:
            tunnel.terminate()
        with contextlib.suppress(Exception):
            httpd.shutdown()
        with contextlib.suppress(Exception):
            httpd.server_close()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    if args.no_public:
        print(f"{YELLOW}[INFO]{RESET} Public URL disabled; press Ctrl+C to stop.")
    else:
        tunnel = start_cloudflared(port)
        if not tunnel:
            tunnel = start_localhost_run(port)
        if not tunnel:
            print(f"{RED}[WARN]{RESET} Could not start any tunnel. Install 'cloudflared' or 'openssh'. Serving locally only.")
        else:
            print(f"{YELLOW}[WAIT]{RESET} Establishing tunnel…")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()

