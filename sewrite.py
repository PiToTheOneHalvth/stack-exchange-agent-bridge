#!/usr/bin/env python3
"""
sewrite.py — Stack Exchange write helper with show-before-send discipline.

Every write command DEFAULTS to dry-run: it prints the exact endpoint and
payload it would send, then exits. Append --send to actually perform the
write. This is deliberate: no write leaves the machine un-reviewed.

Reads (me / inbox / notifications) run immediately.

Credentials come from ~/.hermes/.env (SE_ACCESS_TOKEN, SE_API_KEY), never
from arguments. The token is never printed.
"""
import argparse
import json
import subprocess
import sys
import urllib.parse
from pathlib import Path

ENV = Path.home() / ".hermes" / ".env"
API = "https://api.stackexchange.com/2.3"
UA = "Mozilla/5.0 (research)"


def creds():
    token = key = None
    if ENV.exists():
        for line in ENV.read_text().splitlines():
            if line.startswith("SE_ACCESS_TOKEN="):
                token = line.split("=", 1)[1].strip()
            if line.startswith("SE_API_KEY="):
                key = line.split("=", 1)[1].strip()
    if not token:
        sys.exit("AUTH_ERROR: SE_ACCESS_TOKEN missing from ~/.hermes/.env")
    if not key:
        sys.exit("AUTH_ERROR: SE_API_KEY missing from ~/.hermes/.env")
    return token, key


def api(method, path, params=None, token=None):
    url = f"{API}{path}"
    cmd = ["curl", "-sS", "-m", "30", "--compressed", "-A", UA]
    if token:
        cmd += ["-H", f"Authorization: Bearer {token}"]
    if params:
        if method == "GET":
            # query string — --data-urlencode would silently switch to POST
            url += "?" + urllib.parse.urlencode(params)
        else:
            cmd += ["-X", "POST"]
            for k, v in params.items():
                cmd += ["--data-urlencode", f"{k}={v}"]
    cmd.append(url)
    return subprocess.run(cmd, capture_output=True, text=True)


def summarize(out, label):
    if out.returncode != 0 or not out.stdout.strip():
        print(f"{label}: HTTP transport failed: {out.stderr[:200]}")
        return False
    try:
        d = json.loads(out.stdout)
    except json.JSONDecodeError:
        print(f"{label}: non-JSON response: {out.stdout[:300]}")
        return False
    if d.get("error_id"):
        print(f"{label}: API error {d.get('error_id')} {d.get('error_name')} "
              f"— {d.get('error_message', '')}")
        return False
    items = d.get("items", [])
    print(f"{label}: OK — {len(items)} item(s); quota_remaining: {d.get('quota_remaining')}")
    for it in items[:5]:
        print("   -", (it.get("title") or it.get("body") or "")[:70].replace("\n", " "),
              "|", it.get("link", ""))
    return True


def body_arg(value):
    """Accept a literal string or @file for the body/title/summary args."""
    if value.startswith("@") and len(value) > 1:
        return Path(value[1:]).read_text().strip()
    return value


def main():
    p = argparse.ArgumentParser(description="Stack Exchange write helper (dry-run by default)")
    p.add_argument("--site", default="math", help="SE site (default: math)")
    p.add_argument("--send", action="store_true",
                   help="actually perform the write (default: dry-run print only)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("me", help="who the token acts as")
    ib = sub.add_parser("inbox", help="unread inbox items")
    ib.add_argument("--recent", action="store_true", help="recent items with read/unread flags")
    sub.add_parser("notifications", help="unread notifications")

    cm = sub.add_parser("comment", help="add a comment on a post")
    cm.add_argument("post_id")
    cm.add_argument("body", help="comment text (markdown, <=600 chars) or @file")

    an = sub.add_parser("answer", help="answer a question")
    an.add_argument("question_id")
    an.add_argument("body", help="answer body (markdown) or @file")

    eq = sub.add_parser("edit-q", help="edit a question")
    eq.add_argument("question_id")
    eq.add_argument("body", help="new body (markdown) or @file")
    eq.add_argument("--title", help="new title")
    eq.add_argument("--tags", help="tags, semicolon-separated")
    eq.add_argument("--summary", default="update", help="edit summary")

    ea = sub.add_parser("edit-a", help="edit an answer")
    ea.add_argument("answer_id")
    ea.add_argument("body", help="new body (markdown) or @file")
    ea.add_argument("--summary", default="update", help="edit summary")

    dc = sub.add_parser("delete-comment", help="delete one of your comments")
    dc.add_argument("comment_id")

    vt = sub.add_parser("vote", help="vote on a question/answer/comment")
    vt.add_argument("kind", choices=["q", "a", "c"])
    vt.add_argument("post_id")
    vt.add_argument("direction", choices=["up", "down"], nargs="?", default="up")
    vt.add_argument("--undo", action="store_true")

    ac = sub.add_parser("accept", help="accept an answer on one of your questions")
    ac.add_argument("answer_id")
    ua_ = sub.add_parser("unaccept", help="undo an accept")
    ua_.add_argument("answer_id")

    fl = sub.add_parser("flag", help="flag a post (human-directed only)")
    fl.add_argument("kind", choices=["q", "a", "c"])
    fl.add_argument("post_id")
    fl.add_argument("option_id", help="numeric flag option (see /flags/options)")
    fl.add_argument("--reason", help="flag message where applicable")

    args = p.parse_args()
    token, key = creds()
    site = args.site
    key_params = {"site": site, "key": key}

    method, path, params, label, is_write = "GET", None, None, None, False

    if args.cmd == "me":
        method, path, params, label = "GET", "/me", dict(key_params), "me"
    elif args.cmd == "inbox":
        if args.recent:
            method, path, params, label = "GET", "/me/inbox", {**key_params, "pagesize": "30"}, "inbox recent"
        else:
            method, path, params, label = "GET", "/me/inbox/unread", {**key_params, "pagesize": "30"}, "inbox unread"
    elif args.cmd == "notifications":
        method, path, params, label = "GET", "/me/notifications/unread", dict(key_params), "notifications unread"
    elif args.cmd == "comment":
        method, path, params, label, is_write = "POST", f"/posts/{args.post_id}/comments/add", dict(key_params), f"comment on post {args.post_id}", True
        params["body"] = body_arg(args.body)
    elif args.cmd == "answer":
        method, path, params, label, is_write = "POST", f"/questions/{args.question_id}/answers/add", dict(key_params), f"answer question {args.question_id}", True
        params["body"] = body_arg(args.body)
    elif args.cmd == "edit-q":
        method, path, params, label, is_write = "POST", f"/questions/{args.question_id}/edit", dict(key_params), f"edit question {args.question_id}", True
        params["body"] = body_arg(args.body)
        params["comment"] = args.summary
        if args.title: params["title"] = args.title
        if args.tags: params["tags"] = args.tags
    elif args.cmd == "edit-a":
        method, path, params, label, is_write = "POST", f"/answers/{args.answer_id}/edit", dict(key_params), f"edit answer {args.answer_id}", True
        params["body"] = body_arg(args.body)
        params["comment"] = args.summary
    elif args.cmd == "delete-comment":
        method, path, params, label, is_write = "POST", f"/comments/{args.comment_id}/delete", dict(key_params), f"delete comment {args.comment_id}", True
    elif args.cmd == "vote":
        base = {"q": "questions", "a": "answers", "c": "comments"}[args.kind]
        action = f"{args.direction}vote"
        if args.kind == "c" and args.direction == "down":
            sys.exit("comments can only be upvoted")
        suffix = f"/{action}/undo" if args.undo else f"/{action}"
        method, path, params, label, is_write = "POST", f"/{base}/{args.post_id}{suffix}", dict(key_params), f"{action} {args.kind}{args.post_id}{' (undo)' if args.undo else ''}", True
    elif args.cmd in ("accept", "unaccept"):
        suffix = "/accept" if args.cmd == "accept" else "/accept/undo"
        method, path, params, label, is_write = "POST", f"/answers/{args.answer_id}{suffix}", dict(key_params), f"{args.cmd} answer {args.answer_id}", True
    elif args.cmd == "flag":
        base = {"q": "questions", "a": "answers", "c": "comments"}[args.kind]
        method, path, params, label, is_write = "POST", f"/{base}/{args.post_id}/flags/add", dict(key_params), f"flag {args.kind}{args.post_id}", True
        params["option_id"] = args.option_id
        if args.reason: params["comment"] = args.reason

    if is_write:
        print(f"WOULD {'SEND' if args.send else 'SEND (dry-run)'}: {method} {path}")
        for k, v in params.items():
            if k == "key":
                print(f"  {k}: <hidden>")
            else:
                preview = v if len(v) <= 200 else v[:200] + f"... ({len(v)} chars)"
                print(f"  {k}: {preview}")
        if not args.send:
            print("NOT SENT — add --send to execute.")
            return
        print("--- executing ---")

    out = api(method, path, params, token)
    summarize(out, label or args.cmd)


if __name__ == "__main__":
    main()
