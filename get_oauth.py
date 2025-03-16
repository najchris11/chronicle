import spotipy
from spotipy.oauth2 import SpotifyOAuth
# import mySecrets

REDIRECT_URI = 'http://localhost:8888/callback'
SCOPE = "playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-library-modify user-library-read"

sp_oauth = SpotifyOAuth(
    client_id=mySecrets.SPOTIFY_CLIENT_ID,
    client_secret=mySecrets.SPOTIFY_CLIENT_SECRET,
    client_id = os.environ["SPOTIFY_CLIENT_ID"],
    client_secret = os.environ["SPOTIFY_CLIENT_SECRET"],
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    cache_path=".cache-spotify"  # This will cache the token info locally
)

auth_url = sp_oauth.get_authorize_url()
print("Please navigate to the following URL to authorize:")
print(auth_url)

# After you authorize, you'll be redirected to your redirect URI with a code in the URL.
response_url = input("Paste the full redirect URL here: ")
code = sp_oauth.parse_response_code(response_url)
token_info = sp_oauth.get_access_token(code, as_dict=True)
print("Your token info:", token_info)