# Chronicle

Chronicle is a set of scripts that let you automatically log your Spotify liked songs into monthly playlists. It’s designed to help you chronicle your musical journey over time!

> **Note:**  
> Each user must use their own Spotify API credentials. This repository is meant as a template.
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
- Add any new liked songs **from the last 26 hours** to the current month’s playlist.
- Prevents duplicate additions by checking if a track is already in the monthly playlist.
- Uses a **GitHub Secret (`LAST_RUN_TIMESTAMP`)** to track the last run time and avoid re-processing the same songs.
- Playlists are named in the format `Month Year - Chronicle`

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

## Handling the `LAST_RUN_TIMESTAMP` GitHub Secret

Chronicle maintains a **GitHub Secret (`LAST_RUN_TIMESTAMP`)** to track when the script last ran. This prevents reprocessing the same liked songs multiple times.

### **How It Works**
- The workflow reads `LAST_RUN_TIMESTAMP` before running `main.py`.
- If the secret is missing, it defaults to **fetching songs from the last 26 hours**.
- After a successful run, the secret is updated with the latest timestamp.

### **How to Reset the Timestamp**
If you want to force the script to reprocess songs, delete the `LAST_RUN_TIMESTAMP` secret in **GitHub Settings > Secrets** and re-run the workflow.

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

      - name: Get Last Run Timestamp
        run: |
          echo "LAST_RUN_TIMESTAMP=$(date --utc -d '${{ secrets.LAST_RUN_TIMESTAMP }}' +%Y-%m-%dT%H:%M:%SZ || echo '1970-01-01T00:00:00Z')" >> $GITHUB_ENV

      - name: Run Chronicle script
        env:
          SPOTIFY_CLIENT_ID: ${{ secrets.SPOTIFY_CLIENT_ID }}
          SPOTIFY_CLIENT_SECRET: ${{ secrets.SPOTIFY_CLIENT_SECRET }}
          SPOTIFY_REFRESH_TOKEN: ${{ secrets.SPOTIFY_REFRESH_TOKEN }}
          LAST_RUN_TIMESTAMP: ${{ env.LAST_RUN_TIMESTAMP }}
        run: |
          python main.py

      - name: Update Last Run Timestamp
        run: |
          echo "LAST_RUN_TIMESTAMP=$(date --utc +%Y-%m-%dT%H:%M:%SZ)" >> $GITHUB_ENV
          gh secret set LAST_RUN_TIMESTAMP --body "$LAST_RUN_TIMESTAMP"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
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
