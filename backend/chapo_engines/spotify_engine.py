import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

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
            me = self.sp.me()
            user_info = self.sp.current_user()
            print(f"Spotify Plan (API): {user_info.get('product', 'Unknown')}")

            print(f"✅ Spotify authentication successful. Logged in as: {me['display_name']} ({me['id']})")
        except Exception as e:
            print(f"❌ Spotify Authentication failed: {e}")
            exit()

    def _get_active_device_id(self):
        devices = self.sp.devices()
        if not devices['devices']:
            print("❌ No active Spotify device found.")
            print("➡️ Please open Spotify and play something on your phone or PC.")
            return None
        return devices['devices'][0]['id']

    def transfer_playback(self):
        devices = self.sp.devices()
        if devices['devices']:
            device_id = devices['devices'][0]['id']
            self.sp.transfer_playback(device_id=device_id, force_play=False)        

    def play_song(self, song_name):
        try:
            self.transfer_playback()

            # Clean input
            song_name = song_name.lower().strip()
            if song_name.startswith("play song"):
                song_name = song_name.replace("play song", "", 1).strip()
            elif song_name.startswith("play"):
                song_name = song_name.replace("play", "", 1).strip()

            # Split on "by" to improve query targeting
            query_parts = song_name.split(" by ")
            if len(query_parts) == 2:
                title, artist = query_parts
                search_query = f'track:"{title.strip()}" artist:"{artist.strip()}"'
            else:
                search_query = f'track:"{song_name}"'

            results = self.sp.search(q=search_query, limit=5, type='track')
            if not results['tracks']['items']:
                print(f"❌ No results found for: {search_query}")
                return "Sorry, I couldn't find that song."

            track = results['tracks']['items'][0]
            track_uri = track['uri']
            track_info = f"{track['name']} by {track['artists'][0]['name']}"
            print(f"🎵 Found: {track_info}")

            device_id = self._get_active_device_id()
            if not device_id:
                return "Please start playing any song on Spotify and try again."

            self.sp.start_playback(device_id=device_id, uris=[track_uri])
            return f"Now playing {track_info}."

        except spotipy.exceptions.SpotifyException as e:
            print(f"❌ Spotify error: {e}")
            return "Spotify encountered an error."
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return "Something went wrong while trying to play the song."

if __name__ == "__main__":
    player = SpotifyPlayer()
    while True:
        song = input("\n🎤 Enter a song to play (or type 'exit' to quit): ")
        if song.lower() == 'exit':
            break
        player.play_song(song)
