
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

load_dotenv()

class SpotifyPlayer:
    def __init__(self):
        try:
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
                scope="user-read-playback-state,user-modify-playback-state,user-read-currently-playing,app-remote-control,playlist-read-private"
            ))
            user_info = self.sp.current_user()
            print(f"✅ Spotify authentication successful. Logged in as: {user_info['display_name']} ({user_info['id']})")
            print(f"📦 Plan: {user_info.get('product', 'Unknown')}")
        except Exception as e:
            print(f"❌ Spotify Authentication failed: {e}")
            exit()

    def play_song(self, song_name):
        try:
            results = self.sp.search(q=song_name, limit=1, type='track')
            if not results['tracks']['items']:
                print(f"❌ No results found for: {song_name}")
                return False

            track = results['tracks']['items'][0]
            track_uri = track['uri']
            print(f"🎵 Found: {track['name']} by {track['artists'][0]['name']}")

            devices = self.sp.devices()
            if not devices['devices']:
                print("❌ No active devices found.")
                print("➡️ Please open Spotify on your phone or PC and start playing a song, then try again.")
                return False

            device_id = devices['devices'][0]['id']
            self.sp.start_playback(device_id=device_id, uris=[track_uri])
            print("✅ Song is now playing!")
            return True

        except spotipy.exceptions.SpotifyException as e:
            print(f"❌ Spotify error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

        return False

if __name__ == "__main__":
    player = SpotifyPlayer()
    while True:
        song = input("\n🎤 Enter a song to play (or type 'exit' to quit): ")
        if song.lower() == 'exit':
            break
        player.play_song(song)
