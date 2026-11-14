# Stack Exchange Agent Bridge — OAuth write bridge for an AI assistant

**Tags:** `script` `api`

## About

The Stack Exchange Agent Bridge is an open-source script that connects an AI
assistant running on the user's own machine to the Stack Exchange API through
the official OAuth 2.0 authorization-grant flow (scopes: `write_access`,
`no_expiry`, `read_inbox`). Any registered Stack Exchange user can authorize
the app and receive a token for their own account.

It is **not a content bot**. Every write operation — posting, editing,
commenting, voting, flagging, accepting — is initiated and approved by the
account owner before it is sent. The assistant can also read the owner's
inbox and notifications.

Use cases: managing a Stack Exchange account from the terminal or through an
assistant — draft review, inbox monitoring, vote and flag management — using
only the official API.

## How it works

1. The user runs the authorization flow themselves and logs in with their own
   Stack Exchange credentials. The script never sees a password: it captures
   the OAuth code locally (localhost redirect) and exchanges it for an access
   token stored with owner-only permissions (`chmod 600`), outside the
   repository.
2. All subsequent calls use `Authorization: Bearer <token>`. Writes appear
   under the user's account exactly as if they had used the site.
3. The token can be revoked at any time from the Stack Apps App Management
   page.

## Code

[github.com/PiToTheOneHalvth/stack-exchange-agent-bridge](https://github.com/PiToTheOneHalvth/stack-exchange-agent-bridge) —
`auth_flow.py` handles the OAuth capture and token exchange. Python 3.9+
stdlib plus `curl`; no secrets are ever committed.

## Contact

- Math.SE profile: [pi_to_the_one_halvth](https://math.stackexchange.com/users/1696924)
- GitHub: [PiToTheOneHalvth](https://github.com/PiToTheOneHalvth)

## License

MIT.
