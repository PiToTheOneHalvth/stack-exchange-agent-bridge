# Stack Exchange Agent Bridge

Personal OAuth write bridge for an AI assistant managing a Stack Exchange account
through the official [Stack Exchange API](https://api.stackexchange.com/docs).

It is **not a content bot**. Every write operation — posting, editing, commenting,
voting, flagging, accepting — is initiated and approved by the account owner
before it is sent. The assistant can also read the owner's inbox and
notifications (`read_inbox`), replacing manual browser checking.

## How it works

1. The owner registers an application at [Stack Apps](https://stackapps.com/apps/oauth/register)
   (OAuth domain: `localhost`) and runs the authorization flow themselves, logging
   in with their own Stack Exchange credentials. **The script never sees a password.**
2. `auth_flow.py` listens on `127.0.0.1`, captures the OAuth `code`, and exchanges
   it for an access token (scopes: `write_access`, `no_expiry`, `read_inbox`).
3. The token is stored with owner-only permissions (`chmod 600`) outside this
   repository. **No secrets are ever committed here.**
4. All subsequent API calls use `Authorization: Bearer <token>`; writes appear
   under the owner's account exactly as if they had used the site.

The token can be revoked at any time from the Stack Apps App Management page.

## Usage

```bash
# Step 1 — prints the authorize URL and waits (10 min) for the redirect
python3 auth_flow.py authorize <client_id>

# Step 2 — exchange the captured code for the token
# (stores it in ~/.hermes/.env as SE_ACCESS_TOKEN, chmod 600)
python3 auth_flow.py exchange <client_id> <client_secret>
```

Requires: Python 3.9+ (stdlib only), `curl` for the token exchange.

## License

MIT — see [LICENSE](LICENSE).

## Contact

- Math.SE: [pi_to_the_one_halvth](https://math.stackexchange.com/users/1696924)
- Stack Apps announcement: *(link after publication)*
