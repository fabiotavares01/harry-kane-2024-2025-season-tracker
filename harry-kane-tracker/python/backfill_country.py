import os
import time
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
headers = {"x-apisports-key": API_KEY}

conn = psycopg2.connect(os.getenv("NEON_CONNECTION_STRING"))
cur = conn.cursor()

cur.execute("SELECT team_id FROM teams WHERE country IS NULL")
missing = [row[0] for row in cur.fetchall()]
print(f"Found {len(missing)} teams missing country.")

for team_id in missing:
    response = requests.get(f"{BASE_URL}/teams", headers=headers, params={"id": team_id})
    data = response.json().get("response", [])
    if data:
        country = data[0]["team"]["country"]
        cur.execute("UPDATE teams SET country = %s WHERE team_id = %s", (country, team_id))
        print(f"Team {team_id}: {country}")
    else:
        print(f"Team {team_id}: no data returned")
    conn.commit()
    time.sleep(7)

cur.close()
conn.close()
print("Done.")
