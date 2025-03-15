import os
import sys
import spotipy
from spotipy.oauth2 import SpotifyOAuth
# import mySecrets
from datetime import datetime, timezone
from collections import defaultdict

# # Configuration: these should be set as environment variables
# CLIENT_ID = mySecrets.SPOTIFY_CLIENT_ID
# CLIENT_SECRET = mySecrets.SPOTIFY_CLIENT_SECRET
# REFRESH_TOKEN = mySecrets.SPOTIFY_REFRESH_TOKEN
# REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
# SCOPE = "user-library-read playlist-modify-public playlist-modify-private"
# CACHE_PATH = ".cache-spotify"
# Configuration: These should be set as environment variables
CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["SPOTIFY_REFRESH_TOKEN"]
REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
SCOPE = "user-library-read playlist-modify-public playlist-modify-private"
CACHE_PATH = ".cache-spotify"

def get_spotify_client():
    """Return an authenticated Spotify client using the refresh token."""
    sp_oauth = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=CACHE_PATH
    )
    token_info = sp_oauth.refresh_access_token(REFRESH_TOKEN)
    access_token = token_info["access_token"]
    return spotipy.Spotify(auth=access_token)

def get_monthly_playlist_id(sp, dt):
    """
    Get or create a playlist for the given month-year.
    The playlist name will be in the format 'Chronicle/Month Year'.
    """
    month_name = dt.strftime("%B")
    year = dt.year
    playlist_name = f"{month_name} {year} - Chronicle"
    user_id = sp.current_user()["id"]

    # Retrieve user's playlists in a paginated fashion
    playlist_id = None
    limit = 50
    offset = 0
    while True:
        playlists = sp.current_user_playlists(limit=limit, offset=offset)
        for playlist in playlists["items"]:
            if playlist["name"] == playlist_name:
                playlist_id = playlist["id"]
                break
        if playlist_id or not playlists["next"]:
            break
        offset += limit

    if not playlist_id:
        new_playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=False,
            description=f"Backlog of liked songs for {month_name} {year} created by Chronicle Backlog"
        )
        playlist_id = new_playlist["id"]
        print(f"Created new playlist: {playlist_name}")
    return playlist_id

def get_liked_tracks_since(sp, since_dt):
    """
    Fetch liked tracks with an added_at datetime greater than or equal to since_dt.
    Returns a list of tuples: (track_uri, added_at).
    """
    tracks = []
    limit = 50
    offset = 0
    while True:
        results = sp.current_user_saved_tracks(limit=limit, offset=offset)
        for item in results["items"]:
            # Convert the 'added_at' string to a timezone-aware datetime
            added_at = datetime.fromisoformat(item["added_at"].replace("Z", "+00:00"))
            if added_at >= since_dt:
                tracks.append((item["track"]["uri"], added_at))
        if not results["next"]:
            break
        offset += limit
    return tracks

def add_tracks_to_playlist(sp, playlist_id, track_uris):
    """
    Add tracks to the playlist in batches (Spotify API limit is 100 per request).
    """
    if not track_uris:
        return
    batch_size = 100
    for i in range(0, len(track_uris), batch_size):
        batch = track_uris[i:i + batch_size]
        sp.playlist_add_items(playlist_id, batch)
    print(f"Added {len(track_uris)} track(s) to playlist with ID: {playlist_id}")

def main():
    # Determine the backlog start date from command-line arguments or default to November 1, 2022.
    if len(sys.argv) > 1:
        try:
            backlog_start = datetime.fromisoformat(sys.argv[1])
            if backlog_start.tzinfo is None:
                backlog_start = backlog_start.replace(tzinfo=timezone.utc)
        except Exception as e:
            print("Error parsing date argument. Please use the format YYYY-MM-DD.")
            return
    else:
        backlog_start = datetime(2022, 11, 1, tzinfo=timezone.utc)
    
    print(f"Fetching liked tracks since: {backlog_start.isoformat()}")

    sp = get_spotify_client()
    liked_tracks = get_liked_tracks_since(sp, backlog_start)
    print(f"Found {len(liked_tracks)} liked track(s) since backlog start.")

    # Group tracks by the month they were added.
    monthly_tracks = defaultdict(list)
    for uri, added_at in liked_tracks:
        month_key = added_at.strftime("%Y-%m")  # e.g., "2022-11"
        monthly_tracks[month_key].append(uri)

    # For each month, get or create the corresponding playlist and add the tracks.
    for month_key, track_uris in monthly_tracks.items():
        dt = datetime.strptime(month_key, "%Y-%m").replace(tzinfo=timezone.utc)
        playlist_id = get_monthly_playlist_id(sp, dt)
        print(f"Processing {month_key}: {len(track_uris)} track(s)")
        add_tracks_to_playlist(sp, playlist_id, track_uris)

if __name__ == "__main__":
    main()