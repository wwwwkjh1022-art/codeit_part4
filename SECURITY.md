# Security Notes

## Secret Handling

- Real API keys must stay only in local `.env`.
- Commit only `.env.example`.
- Never commit `.env`, private keys, certificates, or bearer tokens.

## Local Safety Guard

This repository uses a tracked git hook at `.githooks/pre-commit`.

It blocks commits when:

- `.env` or `.env.*` files are staged
- private key or certificate files are staged
- staged content looks like an API key or bearer token

## Recommended Workflow

1. Put real keys in local `.env`
2. Keep placeholders only in `.env.example`
3. Review `git status` before every commit
4. If a secret was exposed anywhere, rotate it immediately
