
# INFOSYS - YouTube Analytics Dashboard

## What is this project?

This project is a website-like app that helps you understand a YouTube channel.

You type a channel ID (starts with `UC...`) or a channel name (starts with `@...`).
Then the app:

1. Gets channel and video data from YouTube.
2. Cleans the data so it is easy to use.
3. Shows charts and numbers.
4. Saves data into a database.
5. Tries to guess future growth from past data.

The app is made with Streamlit, so it runs in your browser.

## What has been done in this repo?

These parts are already built:

1. A full dashboard UI that looks like YouTube Studio (dark/light mode too).
2. YouTube API connection to fetch channel details and videos.
3. Data cleaning and like/comment rate calculations.
4. Many charts for views, likes, comments, trends, categories, and heatmaps.
5. Video search and filters (by keyword, views, date, category, and engagement).
6. Multi-channel comparison screen.
7. PostgreSQL database saving (channels, videos, and summary metrics).
8. A table setup file that creates all needed database tables.
9. Simple future guessing (growth forecast + posting/content suggestions).
10. **AI features (Cloudflare Workers AI — GLM 5.2, free tier):** an "AI Insights"
    page that writes a plain-English performance report, and a "Comment Sentiment"
    page that fetches viewer comments and classifies each as positive/neutral/negative.

## Simple project flow

1. You enter a channel ID or `@username`.
2. App calls YouTube API.
3. App processes data into tables.
4. App shows dashboard pages and charts.
5. App stores data in PostgreSQL.
6. App can compare channels and show prediction ideas.

## Folder and file guide

### Root files

- `README.md`: This documentation file.
- `requirements.txt`: Python packages needed by this project.
- `.gitignore`: Files/folders Git should not track.
- `.env.example`: Safe template file for local settings.
- `.env`: Local secret settings (API key and database password). Keep private.
- `.pre-commit-config.yaml`: Local secret scanner that runs before commit.
- `.github/workflows/secret-scan.yml`: Secret scanner that runs in GitHub Actions.
- `Profile_Pic.mp4`: Video used in the sidebar profile area.


### Documents/

- `Documents/Call Schedule Interns.xlsx`: Project schedule spreadsheet.
- `Documents/Development of a YouTube Analytics and Insight Dashboard for Channel Performance Evaluation and Engagement Analysis.pdf`: Project report document.

### src/

- `src/main.py`: Main Streamlit app. Handles pages, styles, API call flow, and dashboard display.

#### src/dashboard/

- `src/dashboard/charts.py`: All chart-making functions (Plotly).
- `src/dashboard/filters.py`: Search/sort/filter tools for videos.
- `src/dashboard/__init__.py`: Exports dashboard functions.

#### src/youtube_data_collection/

- `src/youtube_data_collection/api_handler.py`: Talks to YouTube Data API.
- `src/youtube_data_collection/data_processor.py`: Cleans and validates data, computes engagement metrics.
- `src/youtube_data_collection/__init__.py`: Empty placeholder file.

#### src/data_storage/

- `src/data_storage/database.py`: PostgreSQL connection setup.
- `src/data_storage/schema.sql`: SQL to create database tables and indexes.
- `src/data_storage/storage_service.py`: Save channel/video/summary data to database.
- `src/data_storage/analytics_queries.py`: SQL queries for trends, content analysis, and channel comparisons.
- `src/data_storage/predictive_analytics.py`: Forecasting and recommendation logic.
- `src/data_storage/__init__.py`: Empty placeholder file.

### tests/

- `tests/`: Python data-processing, storage and session-validation tests.
- `auth-gateway/tests/`: Gateway request-policy and session-revocation tests.

## Pages in the app

1. **Analytics**
Shows main channel numbers, top videos, traffic-like views, and engagement overview.

2. **Video Explorer**
Lets you search and filter videos, then see results in a table and chart.

3. **Trend Analysis**
Shows trend lines, posting patterns, best times, and forecast cards.

4. **Multi-Channel**
Compares many channels side by side and gives simple comparison notes.

5. **AI Insights**
An AI model reads your channel's numbers and writes a short performance report
plus specific action tips. Needs `CLOUDFLARE_API_TOKEN`.

6. **Comment Sentiment**
Fetches viewer comments from your top videos and classifies each as positive,
neutral, or negative with charts and example comments. Needs `CLOUDFLARE_API_TOKEN`.

## What you need before running

1. Python 3.10+ (recommended)
2. PostgreSQL running on your machine (or reachable server)
3. YouTube Data API key

## Setup steps (Windows PowerShell)

1. Create and activate virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install packages:

```powershell
pip install -r requirements.txt
```

3. Copy the safe template to `.env`:

```powershell
Copy-Item .env.example .env
```

4. Open `.env` and add your own values:

```env
YOUTUBE_API_KEY=your_key_here
# For the AI features (Cloudflare Workers AI, free tier — model GLM 5.2).
# Create a Workers AI API token in the Cloudflare dashboard. Leave blank to run
# the app without AI (those two pages show an "add token" note).
CLOUDFLARE_API_TOKEN=your_cloudflare_token_here
# Optional — auto-detected from the token if left blank.
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
DB_HOST=localhost
DB_PORT=5432
DB_NAME=youtube_analytics
DB_USER=postgres
DB_PASSWORD=your_password_here
NEON_AUTH_URL=https://your-neon-auth-host/neondb/auth
```

### Local authentication

Google and email sign-in now use one Neon Auth gateway. The gateway preserves
this app's login design and establishes Secure, HttpOnly browser cookies.
Streamlit checks the session through a private loopback endpoint on every rerun
and before database operations. The old independent `st.login("google")` flow
has been removed from the application code.

Build the gateway with `npm ci` and `npm run build` in `auth-gateway`, then run
this from the repository root for real local email and Google login:

```powershell
.\venv\Scripts\python.exe scripts/run_local.py
```

Open **http://localhost:3001/auth/sign-in**. Keep the terminal open; Ctrl+C stops
the three local services. The launcher uses the private `.env` Neon settings
and creates auth secrets in memory. The [local setup and testing guide](auth-gateway/LOCAL_SETUP.md)
covers Neon settings, verification, password reset and troubleshooting.
Starting `streamlit run` alone will not authenticate. `run_local_preview.py`
is a separate offline layout preview that deliberately denies login.

The `.streamlit/config.toml` defaults target localhost. Private `secrets.toml`
is optional; its previous `[auth.google]` block is unused by the new flow.
The gateway, proxy and Streamlit must be deployed together.

Production origin: `https://ytvideoanalysis.studio`. Google sign-in is disabled
by default pending provider setup, account-linking review and staging tests.
Google client credentials are configured in Neon; they do not belong in
Streamlit secrets or browser code. Provide application runtime secrets through
server-side environment variables. Keep local `.env` files out of Git.

5. Create the PostgreSQL database (example name: `youtube_analytics`).

6. Run SQL schema file `src/data_storage/schema.sql` on that database. (Re-run it
   after updating — it now also creates the `video_comments` table used by the
    Comment Sentiment feature. Legacy `users` and `oauth_users` records are
    retained; the new login flow does not merge or delete them.)

7. Start app:

```powershell
.\venv\Scripts\python.exe scripts/run_local.py
```

## Deployment

Deploy the auth gateway, Streamlit and HTTPS reverse proxy together. Supply
secrets through server-side environment variables and verify provider settings,
migrations, login and session revocation before release. Standalone Streamlit
hosting does not cover the gateway boundary.

## Secret safety checks

1. Install pre-commit:

```powershell
pip install pre-commit
```

2. Turn on local checks:

```powershell
pre-commit install
```

3. Run a full scan anytime:

```powershell
pre-commit run --all-files
```

4. GitHub Actions also runs secret scan on push and pull request.

## If a secret may be leaked

1. Create a new YouTube API key and disable the old key.
2. Change your database password.
3. Update your local `.env` file with new values.
4. Keep `.env` out of git (already handled by `.gitignore`).

## Current status

- Main features are implemented.
- Database save + analytics + prediction parts are present.
- Test folder exists, but real test files are still to be written.

## Quick safety note

Do not share your `.env` file, API key, or database password.

 
