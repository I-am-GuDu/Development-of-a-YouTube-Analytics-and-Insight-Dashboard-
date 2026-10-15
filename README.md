# INFOSYS - YouTube Analytics Dashboard

A Streamlit app for analysing YouTube channels. You sign in, enter a channel ID
(`UC...`, 24 characters) or a handle (`@...`), and the app:

1. Fetches channel and video data from the YouTube Data API.
2. Cleans the data and calculates engagement metrics.
3. Shows charts, filters and comparisons.
4. Saves channels, videos and summary metrics to PostgreSQL.
5. Forecasts growth and suggests posting and content ideas.

Pages: Analytics, Video Explorer, Trend Analysis, Multi-Channel, AI Insights and
Comment Sentiment. The two AI pages use Cloudflare Workers AI. The model is set
in `CF_MODEL` in `src/ai_analysis/client.py`.

## Requirements

- Python 3.11 or newer. `scikit-learn==1.9.0` requires 3.11; the other pinned
  packages accept 3.10 or older. Tested on Python 3.13.
- A PostgreSQL database (local or Neon).
- A YouTube Data API key.
- Optional: a Neon Auth project for Google sign-in, and a Cloudflare Workers AI
  token for the AI pages.

## Setup (Windows PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill in `.env` yourself. Never commit it. Then apply
`src/data_storage/schema.sql` to your database once with any PostgreSQL client.
The app does not run it for you.

### Settings

Settings are read from environment variables (`.env` is loaded automatically)
or from Streamlit secrets.

| Name | Needed | Purpose |
| --- | --- | --- |
| `YOUTUBE_API_KEY` | Yes | Fetching channel and video data. |
| `DATABASE_URL` | Yes, or the `DB_*` group | PostgreSQL connection string. |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | If `DATABASE_URL` is empty | Used instead of `DATABASE_URL`. `DB_PASSWORD` is required. |
| `NEON_AUTH_URL` | For Google sign-in | Neon Auth URL from the Neon console. Must be an `https` URL on a `*.neonauth.*.neon.tech` host ending in `/auth`, or the Google button stays disabled. |
| `AUTH_GOOGLE_ENABLED` | No | Set to `false` to switch Google sign-in off. |
| `APP_ORIGIN` | In deployment | Public site address used for the Google return URL. Leave empty locally (the browser address is used). Must be `https` except for `localhost` / `127.0.0.1`. |
| `CLOUDFLARE_API_TOKEN` | For the AI pages | Workers AI token. Without it the AI pages show a note instead. |
| `CLOUDFLARE_ACCOUNT_ID` | No | Detected from the token if empty. |
| `APP_ENV` | In production | When set to `production`, the database connection must use `sslmode=verify-full` and an absolute `sslrootcert` path to a CA file, so use `DATABASE_URL`. |

## Running locally

From the repository root:

```powershell
.\venv\Scripts\Activate.ps1
streamlit run src/main.py --server.address 127.0.0.1
```

Open the URL Streamlit prints (`http://127.0.0.1:8501` by default).

Without `--server.address`, Streamlit listens on all network interfaces, so
anyone on the same network can reach it. Always pass the flag on a shared
network. In deployment, serve the site over HTTPS only and do not leave the
Streamlit port open to the network.

## Authentication

Sign-in runs inside Streamlit (`src/auth.py`, `src/login_page.py`).

- Email + password: sign-up and login against the app's `users` table.
  Passwords are hashed with bcrypt, need at least 10 characters (72 bytes at
  most), and common ones are refused. Five failed logins lock the email for
  15 minutes.
- Continue with Google: uses Neon Auth's Google provider. Once Google returns,
  the app keeps only its own session and ends the Neon session.

Sessions use the `yt_session` cookie. The database stores only a SHA-256 hash
of the token. Sessions expire after 7 days and are revoked on logout.

One sign-in method per email. An email registered with a password cannot sign
in with Google, and an email first used with Google cannot register a password.
Accounts are not merged.

If Google sign-in shows "Google sign-in is unavailable right now", the reason
is in the server log. Usually the site address (`APP_ORIGIN`, or the local
address) has to be added to Neon Auth's trusted domains.

`auth-gateway/` holds an earlier Next.js sign-in gateway. The Streamlit app no
longer uses it, and its `LOCAL_SETUP.md` refers to a launcher script that no
longer exists.

## Tests

```powershell
python -m pytest tests
```

Five tests in `tests/test_auth.py` reach the database through the
duplicate-identity checks in `src/auth.py`. Without a database, 100 tests pass
and those 5 fail.

To run all of them, use a separate Neon test branch, never the main database.
A plain run uses whatever database `.env` points to. Environment variables
override `.env`, so set the test branch in the shell first:

```powershell
$env:DATABASE_URL = "<test-branch-connection-string>"
python -m pytest tests
```

Apply `src/data_storage/schema.sql` to the test branch once before the first
run.

## Dependencies

`requirements.txt` pins exact versions on purpose. When it used open ranges, a
fresh install would have pulled SQLAlchemy 2.1, which maps a plain
`postgresql://` URL to the psycopg 3 driver. Only psycopg2 is installed, so the
database connection, and with it login, broke. `src/data_storage/database.py`
now names the `postgresql+psycopg2` driver explicitly.

Held back:

- `streamlit==1.54.0`: newer releases replace the web server (Tornado to
  Starlette) and remove the BaseWeb UI library that the custom CSS in
  `src/main.py` targets (`data-baseweb` selectors). Upgrading needs a CSS
  rewrite and an end-to-end login test. See the
  [Streamlit 2026 release notes](https://docs.streamlit.io/develop/quick-reference/release-notes/2026).
- `pandas==2.3.3`: Streamlit 1.54 requires pandas below 3.
- `sqlalchemy==2.0.51`: stays on 2.0 until 2.1 is tested (see above).
- `plotly==6.8.0`: 7.x has not been adopted yet.

Update routine:

1. Create a new branch.
2. Change the pins in `requirements.txt`.
3. `pip install -r requirements.txt`
4. `pip check`
5. `pip-audit` (installed separately)
6. `python -m pytest tests`
7. Check by hand: email sign-up, email login, Google sign-in, logout, and that
   a duplicate identity is refused.

`pytest` is the only test tool in `requirements.txt`. Browser and measurement
tools such as Playwright are not; install them separately and keep them out of
the file.

## Security

- `.env` is git-ignored and never committed. Only the `.env.example` templates
  are tracked.
- gitleaks scans for secrets in a pre-commit hook and in GitHub Actions on every
  push and pull request. To enable it locally:

  ```powershell
  pip install pre-commit
  pre-commit install
  pre-commit run --all-files
  ```

- Keep load-test material (`loadtest/` is git-ignored) and any test accounts out
  of public repositories.
- To report a vulnerability or a leaked secret, contact the maintainers
  privately. Do not open a public issue and do not paste the secret.
- Rotate any credential that was ever committed, even if it was removed later.
  It stays in the git history.

## Known issues and planned work

- Upgrade Streamlit and pandas (CSS rewrite and end-to-end login test needed).
- Add a lock file with hashes.
- Audit the `auth-gateway` dependencies.
- Move the duplicate-identity queries in `src/auth.py` into the database
  helpers so tests do not touch a live database.
- On phones the form panel scrolls inside the card with a hidden scrollbar.

## Project layout

- `src/main.py`: Streamlit entry point, pages and dashboard.
- `src/auth.py`: sign-in, sessions and Google via Neon Auth.
- `src/login_page.py`: login and sign-up page.
- `src/ai_analysis/`: Cloudflare Workers AI client, insights and comment sentiment.
- `src/dashboard/`: charts, filters and theme.
- `src/data_storage/`: database connection, `schema.sql`, storage, analytics queries and forecasts.
- `src/youtube_data_collection/`: YouTube API handler and data processing.
- `tests/`: pytest suite.
- `auth-gateway/`: earlier Next.js gateway (not used by the app).
- `Profile_Pic.mp4`: sidebar intro clip.
- `.env.example`: settings template.
- `.pre-commit-config.yaml`, `.gitleaks.toml`, `.github/workflows/secret-scan.yml`: secret scanning.
