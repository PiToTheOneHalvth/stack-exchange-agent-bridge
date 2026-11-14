# Stack Exchange Agent Bridge — OAuth write bridge for a personal AI assistant

**Tags:** `script` `api`

## About

The Stack Exchange Agent Bridge is a personal-use script that connects an AI
assistant running on my own machine to the Stack Exchange API through the
official OAuth 2.0 authorization-grant flow (scopes: `write_access`,
`no_expiry`, `read_inbox`).

It is **not a content bot**. Every write operation — posting, editing,
commenting, voting, flagging, accepting — is initiated and approved by me,
the account owner, before it is sent. The assistant can also read my inbox
and notifications so I don't need to keep a browser tab open.

Use case: managing my own account on Mathematics Stack Exchange — draft
review, inbox monitoring, vote and flag management — from the terminal /
through my assistant, using only the official API.

## How it works

1. I run the authorization flow myself and log in with my own Stack Exchange
   credentials. The script never sees a password: it captures the OAuth code
   locally (127.0.0.1 redirect) and exchanges it for an access token stored
   with owner-only permissions (`chmod 600`), outside the repository.
2. All subsequent calls use `Authorization: Bearer <token>`. Writes appear
   under my account exactly as if I had used the site.
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
