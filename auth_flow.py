#!/usr/bin/env python3
"""
SE OAuth authorization-grant capture + token exchange.

Usage:
  python3 auth_flow.py authorize <client_id> [--port 8765]
      -> prints the authorize URL, starts a one-shot HTTP listener on
         127.0.0.1:<port>, waits for SE to redirect ?code=... and saves it.
  python3 auth_flow.py exchange <client_id> <client_secret> [--code-file .]
      -> POSTs code to https://stackoverflow.com/oauth/access_token/json,
         prints the token and stores it in ~/.hermes/.env as SE_ACCESS_TOKEN.

Password never appears anywhere in this flow: the human logs in themselves
in their own browser at the authorize step.
"""
import http.server
import json
import os
import socket
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HOME = Path.home()
ENV_FILE = HOME / ".hermes" / ".env"
SCRATCH = HOME / ".hermes" / "cache" / "scratch"
CODE_FILE = SCRATCH / "se_oauth_code.txt"
STATE_FILE = SCRATCH / "se_oauth_state.txt"
REDIRECT_FILE = SCRATCH / "se_oauth_redirect.txt"

AUTHORIZE_URL = "https://stackoverflow.com/oauth"
TOKEN_URL = "https://stackoverflow.com/oauth/access_token/json"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"

SCOPE = "write_access,no_expiry,read_inbox"


class _Handler(http.server.BaseHTTPRequestHandler):
    captured = None
    expect_state = ""

    def do_GET(self):
        q = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(q.query)
        code = params.get("code", [None])[0]
        state = params.get("state", [None])[0]
        err = params.get("error", [None])[0]
        if err:
            _Handler.captured = ("error", err, params.get("error_description", [""])[0])
            body = b"Authorization failed. You can close this tab."
        elif code and (not self.expect_state or state == self.expect_state):
            _Handler.captured = ("ok", code)
            CODE_FILE.write_text(code)
            body = b"Authorized. Code captured. You can close this tab."
        else:
            _Handler.captured = ("bad", self.path)
            body = b"Unexpected redirect. Close this tab and re-run."
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass  # silence


def _get_free_port(preferred):
    for port in (preferred, 0):
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", port))
            got = s.getsockname()[1]
            s.close()
            return got
        except OSError:
            s.close()
    raise SystemExit("no free port")


def authorize(client_id, port=8765):
    port = _get_free_port(port)
    state = f"se{int(time.time())}"
    STATE_FILE.write_text(state)
    redirect_uri = f"http://127.0.0.1:{port}/"
    REDIRECT_FILE.write_text(redirect_uri)
    url = (f"{AUTHORIZE_URL}?client_id={client_id}"
           f"&scope={urllib.parse.quote(SCOPE, safe='')}"
           f"&redirect_uri={urllib.parse.quote(redirect_uri, safe='')}"
           f"&state={state}")
    _Handler.expect_state = state
    srv = http.server.HTTPServer(("127.0.0.1", port), _Handler)
    srv.timeout = 600  # 10 min for the human to click + log in
    print(f"LISTENING on {redirect_uri} (10 min window)", flush=True)
    print("Open this in YOUR browser, log in yourself, and approve:\n", flush=True)
    print(url + "\n", flush=True)
    while _Handler.captured is None:
        srv.handle_request()
    srv.server_close()
    kind, payload = _Handler.captured[:2]
    if kind == "ok":
        print(f"CODE captured -> {CODE_FILE}")
    else:
        print(f"FAILED ({kind}): {payload}")
        sys.exit(1)


def exchange(client_id, client_secret, code_file=None):
    code_file = Path(code_file) if code_file else CODE_FILE
    code = code_file.read_text().strip()
    redirect_uri = REDIRECT_FILE.read_text().strip() if REDIRECT_FILE.exists() \
        else "http://127.0.0.1:8765/"
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,  # MUST match the authorize call exactly
    })
    # curl, not urllib: this Mac's framework python lacks TLS certs
    import subprocess
    out = subprocess.run(
        ["curl", "-sS", "-m", "30", "--compressed", "-A", UA,
         "-H", "Content-Type: application/x-www-form-urlencoded",
         "-d", data, TOKEN_URL],
        capture_output=True, text=True, check=False)
    if out.returncode != 0 or not out.stdout.strip():
        print("exchange failed:", out.stderr or "empty response")
        sys.exit(1)
    try:
        resp = json.loads(out.stdout)
    except json.JSONDecodeError:
        print("non-JSON token response:", out.stdout[:400])
        sys.exit(1)
    token = resp.get("access_token")
    if not token:
        print("exchange failed:", json.dumps(resp))
        sys.exit(1)
    # store: env file, chmod 600, never printed in full
    lines = ENV_FILE.read_text().splitlines() if ENV_FILE.exists() else []
    lines = [l for l in lines if not l.startswith("SE_ACCESS_TOKEN=")]
    lines.append(f"SE_ACCESS_TOKEN={token}")
    ENV_FILE.write_text("\n".join(lines) + "\n")
    ENV_FILE.chmod(0o600)
    print("TOKEN stored in ~/.hermes/.env as SE_ACCESS_TOKEN (chmod 600).")
    print("Scopes granted:", resp.get("scope", "unknown"))
    print("Expires:", resp.get("expires", "never (no_expiry)"))
    print("Token tail for verification:", token[-6:])


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("authorize", "exchange"):
        sys.exit(__doc__)
    if sys.argv[1] == "authorize" and len(sys.argv) >= 3:
        authorize(sys.argv[2])
    elif sys.argv[1] == "exchange" and len(sys.argv) >= 4:
        exchange(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)
