# Local login

Run this from the repository root in PowerShell:

```powershell
.\venv\Scripts\python.exe scripts/run_local.py
```

Open **http://localhost:3001/auth/sign-in** in Chrome. Keep the terminal open.
Ctrl+C stops the gateway, local proxy and Streamlit. Use `localhost`, not the
numeric address. Starting Streamlit alone does not start the login services.

If gateway dependencies or source changed, first run these in `auth-gateway`:

```powershell
npm ci
npm run build
```

The launcher reads `NEON_AUTH_URL` and application settings from the ignored
root `.env` and optional `.env.local`. It creates two independent random auth
secrets in memory on each launch, never prints them, and passes the database
and application API credentials only to Streamlit. No Google client secret is
needed in local source code. Do not paste any secret into chat or commit it.

All three services bind to `127.0.0.1`. Port 3001 is the browser entry point;
3000 is the auth gateway and 8501 is Streamlit. The proxy blocks the internal
session API and checks dashboard requests and WebSocket handshakes. Streamlit
also validates its session before protected work. HTTP is allowed only for this
explicit development origin. Secure, HttpOnly auth cookies remain enabled.

## Neon setup for test accounts

Use the Neon branch matching the private `NEON_AUTH_URL`:

- Keep **Sign-in with Email** enabled and enable **Verify at Sign-up**.
- Keep **Allow Localhost** enabled for this development branch. Neon allows
  localhost ports automatically while this option is enabled.
- Google with **Shared keys** is supported for development. The local launcher
  enables Google for the test-only accounts the owner confirmed. This is not a
  production account-linking audit and does not enable Google's production gate.
- The shared email sender supports verification codes and password reset.
  This UI uses verification codes. Use an inbox you control; the shared sender
  may rate-limit repeated attempts. Never mark an email verified directly in SQL.

Sources: [Neon development OAuth](https://neon.com/docs/auth/guides/setup-oauth),
[localhost domains](https://neon.com/docs/auth/guides/configure-domains),
[email provider requirements](https://neon.com/docs/auth/production-checklist).

## Test the complete flow

1. Choose **Continue with Google**, finish consent, and confirm the dashboard
   loads. Sign out using the app's sign-out page.
2. Create an email/password account with an inbox you control, open **Enter
   verification code**, request a code if needed, and verify it. An existing
   unverified test account can use **Verify email** from the sign-in page.
3. Sign in with email/password and confirm the dashboard loads. A Google-only
   account may need **Forgot password?** to establish a password if the managed
   provider permits it; do not expect Google to create a password for you.
4. Use **Forgot password?**, follow the email link in the same browser, choose
   a new password, and confirm the old password fails and the new one works.
5. Open a second dashboard tab. Sign out in the first; refreshing or acting in
   the second must reject the old session. Idle tabs poll every 60 seconds, but
   background-browser throttling can delay the visible update.

The two existing application users and the two Neon Auth users were counted
read-only; no accounts were deleted or migrated. User IDs, not email strings,
identify authenticated users. Production linking behavior still needs review.

## Troubleshooting

- **Sign-in unavailable:** use the launcher above, check the terminal is still
  running, then run `python scripts/check_local_auth.py`. It outputs connection
  status and user counts only. It never prints connection strings or users.
- **Port busy:** stop the earlier local launcher/preview. Do not start both.
- **Verify email:** use the verification page with the same email address.
- **Google returns to login:** report the visible message, without copying the
  callback URL, cookies, or browser network log. OAuth needs a real browser
  round trip; a mocked preview cannot complete it.
- **No email arrives:** check spam and Neon's email/verification settings. Wait
  before retrying; both the provider and local gateway limit requests.

`.streamlit/config.toml` remains required for this Streamlit app's settings.
The previous private `[auth.google]` block in `secrets.toml` is unused by this
flow. You may remove that obsolete block privately after confirming no other
app uses it; keep any unrelated secrets. The launcher does not read that block.

`run_local_preview.py` is only an offline UI preview and cannot sign anyone in.

## Deployment handoff

Nothing here updates EC2. The teammate must deploy the gateway, Streamlit and
HTTPS reverse proxy together; a plain pull/restart of Streamlit is insufficient.
Use `deploy/README.md` as an example to adapt, not an already-validated server
configuration. Production requires independent persistent secrets, its own
Google credentials in Neon, email delivery settings, account-linking review,
data-access review and actual HTTPS login/revocation tests. Do not deploy this
development launcher or enable its test-account exception on EC2.
