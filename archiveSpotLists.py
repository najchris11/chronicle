import os
import spotipy
import mySecrets
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime, timedelta, timezone

# Configuration: these should be set as environment variables
CLIENT_ID = mySecrets.SPOTIFY_CLIENT_ID
CLIENT_SECRET = mySecrets.SPOTIFY_CLIENT_SECRET
REFRESH_TOKEN = mySecrets.SPOTIFY_REFRESH_TOKEN
# The redirect URI is still needed for constructing the OAuth object even if it won't be used interactively.
REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
 # Define required scope
SCOPE = "playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-library-modify user-library-read"
# Cache path (not used interactively now, but required for SpotifyOAuth)
CACHE_PATH = ".cache-spotify"
 
#  # Configuration: These should be set as environment variables
# CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
# CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
# REFRESH_TOKEN = os.environ["SPOTIFY_REFRESH_TOKEN"]
#  # The redirect URI is still needed for constructing the OAuth object even if it won't be used interactively.
# REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
# SCOPE = "playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-library-modify user-library-read"
# CACHE_PATH = ".cache-spotify"

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

def get_release_radar_id(sp):
    limit = 50
    offset = 0
    playlist_id = None
    while True:
        playlists = sp.current_user_playlists(limit=limit, offset=offset)
        for playlist in playlists['items']:
            print(f"DEBUG: Found playlist '{playlist['name']}' owned by '{playlist['owner']['id']}' (ID: {playlist['id']})")
            if playlist['name'] == "Release Radar" and playlist['owner']['id'] == "spotify":
                playlist_id = playlist['id']
                break
        if playlist_id or not playlists['next']:
            break
        offset += limit

    if not playlist_id:
        print("WARNING: Could not find a Release Radar playlist in your library. Fallback ID will likely not work, as Release Radar is user-specific.")
        playlist_id = "37i9dQZEVXblWkHSVjEqnb"  # Replace with your actual Release Radar ID if needed

    print(f"Using Release Radar playlist ID: {playlist_id}")
    return playlist_id

def get_decade_archive_playlist_name():
    year = datetime.now(timezone.utc).year
    decade_start = (year // 10) * 10
    return f"Release Radar Archive {decade_start}s"

def get_or_create_decade_archive_playlist(sp, user_id):
    playlist_name = get_decade_archive_playlist_name()
    limit = 50
    offset = 0
    playlist_id = None
    while True:
        playlists = sp.current_user_playlists(limit=limit, offset=offset)
        for playlist in playlists['items']:
            if playlist['name'] == playlist_name and playlist['owner']['id'] == user_id:
                playlist_id = playlist['id']
                break
        if playlist_id or not playlists['next']:
            break
        offset += limit

    if not playlist_id:
        new_playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=False,
            description=f"Release Radar archive for the {playlist_name[-5:]}"
        )
        playlist_id = new_playlist["id"]
        print(f"Created new archive playlist: {playlist_name}")
    else:
        print(f"Found existing archive playlist: {playlist_name}")

    return playlist_id


def get_existing_playlist_tracks(sp, playlist_id):
    """
    Fetch all track URIs in the given playlist, with error handling.
    """
    existing_tracks = set()
    limit = 100
    offset = 0
    while True:
        try:
            results = sp.playlist_tracks(
                playlist_id,
                fields="items.track.uri,next",
                limit=limit,
                offset=offset
            )
        except spotipy.exceptions.SpotifyException as e:
            print(f"ERROR: Could not fetch tracks for playlist ID {playlist_id}: {e}")
            # Optionally, print the full traceback for deeper debugging:
            # import traceback; traceback.print_exc()
            return set()
        except Exception as e:
            print(f"Unexpected error while fetching playlist {playlist_id}: {e}")
            return set()

        for item in results.get("items", []):
            if item["track"] and item["track"]["uri"]:
                existing_tracks.add(item["track"]["uri"])
        if not results.get("next"):
            break
        offset += limit
    return existing_tracks


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
    user_id = sp.current_user()["id"]

    # 1. Get Release Radar playlist ID
    rr_id = get_release_radar_id(sp)
    rr_tracks = list(get_existing_playlist_tracks(sp, rr_id))

    # 2. Get or create the decade archive playlist
    archive_id = get_or_create_decade_archive_playlist(sp, user_id)

    # 3. Fetch existing tracks in the archive playlist
    existing_archive_tracks = get_existing_playlist_tracks(sp, archive_id)

    # 4. Only add tracks that aren't already in the archive
    tracks_to_add = [track for track in rr_tracks if track not in existing_archive_tracks]

    if tracks_to_add:
        add_tracks_to_playlist(sp, archive_id, tracks_to_add)
        print(f"Archived {len(tracks_to_add)} new Release Radar track(s) to {get_decade_archive_playlist_name()}")
    else:
        print("No new tracks to archive.")

if __name__ == "__main__":
    main()
