import os
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
headers = {"x-apisports-key": API_KEY}

conn = psycopg2.connect(os.getenv("NEON_CONNECTION_STRING"))
cur = conn.cursor()

PLAYER_ID = 184

response = requests.get(f"{BASE_URL}/players/profiles", headers=headers, params={"player": PLAYER_ID})
player_data = response.json()["response"][0]["player"]
cur.execute("UPDATE players SET photo_url = %s WHERE player_id = %s", (player_data["photo"], PLAYER_ID))

conn.commit()
cur.close()
conn.close()
print("Done — Kane's photo added.")
