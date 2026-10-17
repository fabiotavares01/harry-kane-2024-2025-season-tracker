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

PLAYER_ID = 184
ENGLAND_TEAM_ID = 10
SEASON = 2024

COMPETITIONS = {
    5: "UEFA Nations League",
    10: "Friendlies"
}

for league_id, league_name in COMPETITIONS.items():
    print(f"\n--- Checking {league_name} (league {league_id}) ---")

    response = requests.get(f"{BASE_URL}/fixtures", headers=headers, params={
        "team": ENGLAND_TEAM_ID, "league": league_id, "season": SEASON
    })
    fixtures = response.json().get("response", [])
    print(f"Found {len(fixtures)} England fixtures in this competition.")

    for fixture in fixtures:
        fid = fixture["fixture"]["id"]
        date = fixture["fixture"]["date"][:10]
        home = fixture["teams"]["home"]
        away = fixture["teams"]["away"]
        home_score = fixture["goals"]["home"]
        away_score = fixture["goals"]["away"]

        stats_response = requests.get(f"{BASE_URL}/fixtures/players", headers=headers, params={"fixture": fid})
        teams_data = stats_response.json().get("response", [])

        kane_entry = None
        for team_block in teams_data:
            for player_entry in team_block.get("players", []):
                if player_entry["player"]["id"] == PLAYER_ID:
                    kane_entry = player_entry
                    break

        if kane_entry is None:
            print(f"Match {fid} ({date}): Kane not called up — skipping")
            time.sleep(7)
            continue

        for team in (home, away):
            cur.execute("""
                INSERT INTO teams (team_id, name, logo_url)
                VALUES (%s, %s, %s)
                ON CONFLICT (team_id) DO UPDATE SET logo_url = EXCLUDED.logo_url
            """, (team["id"], team["name"], team["logo"]))

        cur.execute("""
            INSERT INTO matches (match_id, match_date, competition_id, season, team_id, home_team, away_team, home_score, away_score, home_team_id, away_team_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (match_id) DO UPDATE SET
                home_score = EXCLUDED.home_score,
                away_score = EXCLUDED.away_score
        """, (fid, date, league_id, f"{SEASON}/{SEASON+1}", ENGLAND_TEAM_ID, home["name"], away["name"], home_score, away_score, home["id"], away["id"]))

        stats = kane_entry["statistics"][0]
        minutes = stats["games"]["minutes"] or 0
        goals = stats["goals"]["total"] or 0
        assists = stats["goals"]["assists"] or 0
        shots_total = stats["shots"]["total"] or 0
        shots_on = stats["shots"]["on"] or 0
        yellow = stats["cards"]["yellow"] or 0
        red = stats["cards"]["red"] or 0
        rating = stats["games"]["rating"]

        cur.execute("""
            INSERT INTO player_match_stats
                (player_id, match_id, minutes_played, goals, assists, shots_total, shots_on_target, yellow_cards, red_cards, rating)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (player_id, match_id) DO UPDATE SET
                minutes_played = EXCLUDED.minutes_played,
                goals = EXCLUDED.goals,
                assists = EXCLUDED.assists,
                shots_total = EXCLUDED.shots_total,
                shots_on_target = EXCLUDED.shots_on_target,
                yellow_cards = EXCLUDED.yellow_cards,
                red_cards = EXCLUDED.red_cards,
                rating = EXCLUDED.rating,
                pulled_at = NOW()
        """, (PLAYER_ID, fid, minutes, goals, assists, shots_total, shots_on, yellow, red, rating))

        status = "played" if minutes > 0 else "on bench, unused"
        print(f"Match {fid} ({date}): Kane {status} ({minutes} mins)")

        conn.commit()
        time.sleep(7)

cur.close()
conn.close()
print("\nDone.")
