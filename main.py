import os
import spotipy
# import mySecrets
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime, timedelta, timezone

# # Configuration: these should be set as environment variables
 # CLIENT_ID = mySecrets.SPOTIFY_CLIENT_ID
 # CLIENT_SECRET = mySecrets.SPOTIFY_CLIENT_SECRET
 # REFRESH_TOKEN = mySecrets.SPOTIFY_REFRESH_TOKEN
 # # The redirect URI is still needed for constructing the OAuth object even if it won't be used interactively.
 # REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
 # # Define required scope
 # SCOPE = "playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-library-modify user-library-read"
 # # Cache path (not used interactively now, but required for SpotifyOAuth)
 # CACHE_PATH = ".cache-spotify"
 
 # Configuration: These should be set as environment variables
CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["SPOTIFY_REFRESH_TOKEN"]
 # The redirect URI is still needed for constructing the OAuth object even if it won't be used interactively.
REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
SCOPE = "playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-library-modify user-library-read"
CACHE_PATH = ".cache-spotify"

# Fetch last run timestamp from GitHub Secret
LAST_RUN_TIMESTAMP = os.environ.get("LAST_RUN_TIMESTAMP") or (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
# Convert to datetime object
last_run = datetime.fromisoformat(LAST_RUN_TIMESTAMP.replace("Z", "+00:00"))
now = datetime.now(timezone.utc)

# Ensure we always fetch from at least the last 26 hours
if now - last_run < timedelta(hours=26):
    last_run = now - timedelta(hours=26)

print(f"Fetching liked tracks since: {last_run.isoformat()}")


def get_spotify_client():
    """
    Returns an authenticated Spotify client using the refresh token.
    """
    sp_oauth = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=CACHE_PATH
    )
    # Use the stored refresh token to get a new access token.
    token_info = sp_oauth.refresh_access_token(REFRESH_TOKEN)
    access_token = token_info["access_token"]
    return spotipy.Spotify(auth=access_token, requests_timeout=30)

def get_monthly_playlist_id(sp):
    """
    Get or create a playlist for the current month (e.g., 'Chronicle - March 2025').
    """
    now = datetime.now()
    month_name = now.strftime("%B")
    year = now.year
    playlist_name = f"{month_name} {year} - Chronicle"

    # Get current user's id
    current_user = sp.current_user()
    user_id = current_user["id"]

    # Retrieve user's playlists (paginated)
    playlist_id = None
    limit = 50
    offset = 0
    while True:
        playlists = sp.current_user_playlists(limit=limit, offset=offset)
        # print(playlists)
        for playlist in playlists['items']:
            if playlist['name'] == playlist_name:
                playlist_id = playlist['id']
                break
        if playlist_id or not playlists['next']:
            break
        offset += limit

    # Create the playlist if it doesn't exist
    if not playlist_id:
        new_playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=False,
            description="Monthly log of liked songs created by Chronicle"
        )
        playlist_id = new_playlist['id']
        print(f"Created new playlist: {playlist_name}")

    return playlist_id


def get_existing_playlist_tracks(sp, playlist_id):
    """
    Fetch existing tracks in the monthly playlist to prevent duplicates.
    """
    existing_tracks = set()
    limit = 100
    offset = 0
    while True:
        results = sp.playlist_tracks(playlist_id, fields="items.track.uri, next", limit=limit, offset=offset)
        
        # Ensure 'items' key exists
        if "items" in results:
            for item in results["items"]:
                existing_tracks.add(item["track"]["uri"])

        # Check if 'next' exists before accessing it
        if "next" not in results or not results["next"]:
            break

        offset += limit

    return existing_tracks

def get_new_liked_tracks(sp, since_dt):
    """
    Return a list of track URIs for liked songs added since a given datetime.
    """
    new_tracks = []
    limit = 50
    offset = 0
    while True:
        results = sp.current_user_saved_tracks(limit=limit, offset=offset)
        for item in results["items"]:
            # 'added_at' is in ISO 8601 format (UTC)
            added_at = datetime.fromisoformat(item["added_at"].replace("Z", "+00:00"))
            if added_at > since_dt:
                new_tracks.append(item["track"]["uri"])
        if results["next"] is None:
            break
        offset += limit
    return new_tracks

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
    print(f"Added {len(track_uris)} track(s) to the playlist.")

def main():
    # Initialize Spotify client using the refresh token
    sp = get_spotify_client()

    # Determine the monthly playlist to use
    playlist_id = get_monthly_playlist_id(sp)

    # Fetch existing tracks in the playlist
    existing_tracks = get_existing_playlist_tracks(sp, playlist_id)

    new_tracks = get_new_liked_tracks(sp, last_run)

    new_tracks = [track for track in new_tracks if track not in existing_tracks]


    if new_tracks:
        print(f"Found {len(new_tracks)} new liked track(s) since {last_run.isoformat()}.")
        add_tracks_to_playlist(sp, playlist_id, new_tracks)
    else:
        print("No new liked tracks found.")

if __name__ == "__main__":
    main()