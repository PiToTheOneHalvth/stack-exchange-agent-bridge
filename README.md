# Stack Exchange Agent Bridge

Open-source OAuth write bridge connecting an AI assistant to the
[Stack Exchange API](https://api.stackexchange.com/docs). Any registered Stack
Exchange user can authorize the app and receive a token for **their own
account**.

It is **not a content bot**. Every write operation — posting, editing, commenting,
voting, flagging, accepting — is initiated and approved by the account owner
before it is sent. The assistant can also read the owner's inbox and
notifications (`read_inbox`), replacing manual browser checking.

## How it works

1. The user registers an application at [Stack Apps](https://stackapps.com/apps/oauth/register)
   (OAuth domain: `localhost`) and runs the authorization flow themselves, logging
   in with their own Stack Exchange credentials. **The script never sees a password.**
2. `auth_flow.py` listens on `127.0.0.1`, captures the OAuth `code`, and exchanges
   it for an access token (scopes: `write_access`, `no_expiry`, `read_inbox`).
3. The token is stored with owner-only permissions (`chmod 600`) outside this
   repository. **No secrets are ever committed here.**
4. All subsequent API calls use `Authorization: Bearer <token>`; writes appear
   under the user's account exactly as if they had used the site.

The token can be revoked at any time from the Stack Apps App Management page.

## Usage

```bash
# Step 1 — prints the authorize URL and waits (10 min) for the redirect
python3 auth_flow.py authorize <client_id>

# Step 2 — exchange the captured code for the token
# (stores it in ~/.hermes/.env as SE_ACCESS_TOKEN, chmod 600)
python3 auth_flow.py exchange <client_id> <client_secret>
```

### sewrite.py — owner-approved write helper

Every write command defaults to **dry-run** (prints the exact endpoint and
payload, sends nothing); append `--send` to perform it.

```bash
python3 sewrite.py me                     # who the token acts as
python3 sewrite.py inbox                  # unread inbox items (network-wide)
python3 sewrite.py inbox --recent         # recent items with read/unread flags
python3 sewrite.py notifications          # unread notifications
python3 sewrite.py comment 12345 "text"   # dry-run; add --send to post
python3 sewrite.py answer 12345 @body.md  # answer from a markdown file
python3 sewrite.py edit-q 12345 @new.md --title "New title" --summary "why"
python3 sewrite.py vote a 12345 up        # vote up/down q|a|c, --undo to reverse
python3 sewrite.py accept 12345           # accept an answer on your question
python3 sewrite.py flag a 12345 25 --reason "..."   # human-directed flags only
```

Requires: Python 3.9+ (stdlib only), `curl` for the token exchange.

## License

MIT — see [LICENSE](LICENSE).

## Contact

- Math.SE: [pi_to_the_one_halvth](https://math.stackexchange.com/users/1696924)
- Stack Apps announcement: *(link after publication)*
