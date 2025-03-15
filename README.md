# Chronicle

Chronicle is a set of scripts that let you automatically log your Spotify liked songs into monthly playlists. It’s designed to help you chronicle your musical journey over time!

> **Note:**  
> Each user must use their own Spotify API credentials. This repository is meant as a template. Non-technical users may find it easier to follow the instructions provided here, or you might consider building a web app for an even smoother experience.

---

## Overview of Scripts

### 1. `get_oauth.py`
This script is used to perform the initial OAuth flow with Spotify using [Spotipy](https://spotipy.readthedocs.io/). It:
- Opens the authorization URL so you can log in and grant permissions.
- Prompts you to paste the redirect URL.
- Extracts and displays your **refresh token** (along with the access token).

**Usage:**

```bash
python get_oauth.py
```

After running, copy the refresh token and store it (for example, as a GitHub secret).

---

### 2. `main.py`
This script uses your stored credentials and refresh token to:
- Refresh your access token automatically.
- Check your current liked (saved) tracks.
- Add any new liked songs (from the past day by default) to the current month’s playlist.
- Playlists are named in the format `Month Year - Chronicle`.

**Usage:**

```bash
python main.py
```

---

### 3. `backlog.py`
This script is used to backfill your playlists by processing your liked songs from a specified start date until now. It:
- Accepts a start date as a command-line parameter (default is November 1, 2022).
- Fetches all liked tracks added since that date.
- Groups tracks by the month they were added.
- Creates (or reuses) monthly playlists named in the format `Month Year - Chronicle`.
- Adds the corresponding tracks to each monthly playlist.

**Usage:**

```bash
# Use the default start date (2022-11-01):
python backlog.py

# Or specify a different start date (YYYY-MM-DD):
python backlog.py 2023-01-01
```

---

## Getting Started

1. **Fork this repository** (or use it as a template) and clone it locally.
2. **Create a Spotify Developer App:**
   - Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
   - Create a new app and note your **Client ID** and **Client Secret**.
   - Add a redirect URI (e.g., `http://localhost:8888/callback`).
3. **Obtain a Refresh Token:**
   - Fill in your `CLIENT_ID` and `CLIENT_SECRET` in `get_oauth.py` (or set them as environment variables).
   - Run the script and follow the instructions to get your refresh token.
4. **Configure Environment Variables:**
   - For local use, you can create a `.env` file or set environment variables in your terminal:
     - `SPOTIFY_CLIENT_ID`
     - `SPOTIFY_CLIENT_SECRET`
     - `SPOTIFY_REFRESH_TOKEN`
5. **Run the Scripts:**
   - Use `get_oauth.py` once to get your token.
   - Use `main.py` to update your current monthly playlist.
   - Use `backlog.py` to backfill your liked songs starting from a specified date.

---

## GitHub Actions

Chronicle offers two GitHub Actions:

### 1. `main.yml` (Daily Logging)
This workflow runs **daily at midnight UTC** and can also be triggered manually to update the current month’s playlist with newly liked songs.

Create `.github/workflows/main.yml`:

```yaml
name: Chronicle

on:
  schedule:
    - cron: "0 0 * * *"
  workflow_dispatch:

jobs:
  run-chronicle:
    runs-on: ubuntu-latest
    
    steps:
      - name: Check out repository code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.9"

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run Chronicle script
        env:
          SPOTIFY_CLIENT_ID: ${{ secrets.SPOTIFY_CLIENT_ID }}
          SPOTIFY_CLIENT_SECRET: ${{ secrets.SPOTIFY_CLIENT_SECRET }}
          SPOTIFY_REFRESH_TOKEN: ${{ secrets.SPOTIFY_REFRESH_TOKEN }}
        run: |
          python main.py
```

### 2. `backlog.yml` (Manual Backlog Processing)
This workflow allows users to **manually trigger** a backlog run for adding old liked songs to monthly playlists.

Create `.github/workflows/backlog.yml`:

```yaml
name: Backlog Run

on:
  workflow_dispatch:
    inputs:
      start_date:
        description: 'Backlog start date in YYYY-MM-DD format'
        required: false
        default: '2022-11-01'

jobs:
  run-backlog:
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.9"

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run backlog script
        env:
          SPOTIFY_CLIENT_ID: ${{ secrets.SPOTIFY_CLIENT_ID }}
          SPOTIFY_CLIENT_SECRET: ${{ secrets.SPOTIFY_CLIENT_SECRET }}
          SPOTIFY_REFRESH_TOKEN: ${{ secrets.SPOTIFY_REFRESH_TOKEN }}
        run: |
          python backlog.py ${{ github.event.inputs.start_date }}
```

### How It Works:
- **`main.yml` runs automatically every day** and updates your current month’s playlist.
- **`backlog.yml` is manually triggered** and lets you specify a backlog start date.

---

## Conclusion

Chronicle offers both an ongoing process (`main.py`) for current updates and a backlog process (`backlog.py`) for retroactively logging your liked tracks. With clear instructions and separate GitHub Actions for automatic logging and manual backlogging, even non-technical users can get started with minimal setup (after obtaining their own Spotify API credentials).

Feel free to fork, modify, or extend the project to better suit your needs!

