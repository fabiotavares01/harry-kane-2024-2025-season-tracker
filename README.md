# Harry Kane: 2024/2025 Season Performance Tracker

Tracking Harry Kane's performance across club and international football in the 2024/2025 season, built on a live-sourced relational data pipeline.

![Dashboard preview](assets/DashboarD.png)

<!-- [![Power BI Dashboard](https://img.shields.io/badge/Power%20BI-View%20Dashboard-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)](YOUR_DASHBOARD_LINK_HERE) -->

---

## Table of Contents

- [Overview](#overview)
- [Dataset](#dataset)
- [Project Pipeline](#project-pipeline)
- [Data Cleaning & Transformation](#data-cleaning--transformation)
- [Dashboard](#dashboard)
- [Key Findings](#key-findings)
- [Limitations](#limitations)

---

## Overview

**Who is Harry Kane:** Harry Kane is an English football player who currently plays for FC Bayern München and represents the England national team. Harry is 33 years old and plays in the striker position. He arrived at FC Bayern München in the 2023/2024 season, and this project covers his second season at the club, along with all the matches he played for his national team across that same season.

**Central Question:** This project is a report on Harry Kane's performance in the 2024/2025 season, across all the different competitions he played in.

---

## Dataset

**Source**

Data was sourced from [API-FOOTBALL](https://www.api-football.com).

**Tables**

| Table | Description |
|---|---|
| `competitions` | Name, country, and type for each competition Harry Kane played in this season |
| `matches` | Every Bayern fixture that season, regardless of whether Kane played, plus England matches where he was in the squad |
| `player_match_stats` | Per-match stats from all the games Kane played |
| `players` | Harry Kane's player information |
| `teams` | All club and national teams involved (Kane's own teams and their opponents), including name, country, continent, and logo |

**Volume**

- 5 unique competitions
- 58 unique matches
- 53 player match stats
- 1 unique player
- 35 unique teams

---

## Project Pipeline

```
API-Football  →  Python (requests, psycopg2)  →  PostgreSQL (Neon)  →  Power BI
```

This project uses four components: **API-Football** as the data source, **Python** for ingestion, **PostgreSQL** (hosted on Neon) for storage, and **Power BI** for visualization.

### 1. Looking up the right IDs

Before pulling any data, I first needed to find the correct IDs for the entities involved, since the API identifies players, teams, and competitions by ID rather than name. I used `lookup_ids.py` to search the API directly for Harry Kane's player ID, Bayern Munich's and England's team IDs, and the relevant competition IDs (Bundesliga, Champions League, DFB-Pokal, Nations League, Friendlies).

<details>
<summary><code>lookup_ids.py</code></summary>

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
headers = {"x-apisports-key": API_KEY}

# --- Lookup 1: Bayern Munich's team ID ---
# Note: "name" parameter requires an exact match; "search" allows partial matching
response = requests.get(f"{BASE_URL}/teams", headers=headers, params={"search": "Bayern"})
data = response.json()
print("=== TEAM SEARCH: 'Bayern' ===")
for item in data.get("response", []):
    team = item["team"]
    print(f"Name: {team['name']} | ID: {team['id']} | Country: {team['country']}")
# Result used: Bayern München | ID: 157

# --- Lookup 2: Harry Kane's player ID ---
response = requests.get(f"{BASE_URL}/players/profiles", headers=headers, params={"search": "Harry Kane"})
data = response.json()
print("\n=== PLAYER SEARCH: 'Harry Kane' ===")
for item in data.get("response", []):
    player = item["player"]
    print(f"Name: {player['name']} | ID: {player['id']} | Nationality: {player['nationality']}")
# Result used: Harry Kane | ID: 184

# --- Lookup 3: England national team ID ---
# Filtered to national == True to exclude club teams named "England" variants
response = requests.get(f"{BASE_URL}/teams", headers=headers, params={"search": "England"})
data = response.json()
print("\n=== NATIONAL TEAMS: 'England' ===")
for item in data.get("response", []):
    team = item["team"]
    if team["national"] == True:
        print(f"Name: {team['name']} | ID: {team['id']} | Country: {team['country']}")
# Result used: England | ID: 10

# --- Lookup 4: UEFA Nations League competition ID ---
response = requests.get(f"{BASE_URL}/leagues", headers=headers, params={"search": "Nations League"})
data = response.json()
print("\n=== COMPETITION SEARCH: 'Nations League' ===")
for item in data.get("response", []):
    league = item["league"]
    country = item["country"]["name"]
    print(f"Name: {league['name']} | ID: {league['id']} | Country: {country}")
# Result used: UEFA Nations League | ID: 5

# --- Lookup 5: Friendlies competition ID ---
response = requests.get(f"{BASE_URL}/leagues", headers=headers, params={"search": "Friendlies"})
data = response.json()
print("\n=== COMPETITION SEARCH: 'Friendlies' ===")
for item in data.get("response", []):
    league = item["league"]
    country = item["country"]["name"]
    print(f"Name: {league['name']} | ID: {league['id']} | Country: {country}")
# Result used: Friendlies | ID: 10 (senior internationals, distinct from
# Friendlies Women (666) and Friendlies Clubs (667))

# --- Lookup 6: Euro 2024 — checked, not used ---
response = requests.get(f"{BASE_URL}/leagues", headers=headers, params={"search": "Euro"})
data = response.json()
print("\n=== COMPETITION SEARCH: 'Euro' ===")
for item in data.get("response", []):
    league = item["league"]
    country = item["country"]["name"]
    print(f"Name: {league['name']} | ID: {league['id']} | Country: {country}")
# Not used: Euro 2024 falls under the 2023/2024 season, outside this project's scope

# --- Lookup 7: World Cup Qualifiers — checked, not used ---
# Filtered to season=2024 to confirm competition is active for the season in scope
response = requests.get(f"{BASE_URL}/leagues", headers=headers, params={
    "search": "World Cup",
    "season": 2024
})
data = response.json()
print("\n=== COMPETITION SEARCH: 'World Cup' (season 2024) ===")
for item in data.get("response", []):
    league = item["league"]
    country = item["country"]["name"]
    print(f"Name: {league['name']} | ID: {league['id']} | Country: {country}")
# No results returned — 2026 World Cup qualifiers began in 2025, outside this
# project's 2024/2025 season scope
```

</details>

### 2. Seeding reference data

With the IDs confirmed, I used `seed_reference_data.py` to insert the core reference data (Bayern Munich, Harry Kane, and Bundesliga) into the `teams`, `players`, and `competitions` tables.

<details>
<summary><code>seed_reference_data.py</code></summary>

```python
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv("NEON_CONNECTION_STRING"))
cur = conn.cursor()

cur.execute("""
    INSERT INTO teams (team_id, name, country)
    VALUES (%s, %s, %s)
    ON CONFLICT (team_id) DO NOTHING
""", (157, "Bayern München", "Germany"))

cur.execute("""
    INSERT INTO players (player_id, name, team_id, position, nationality)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (player_id) DO NOTHING
""", (184, "Harry Kane", 157, "Attacker", "England"))

cur.execute("""
    INSERT INTO competitions (competition_id, name, country, type)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (competition_id) DO NOTHING
""", (78, "Bundesliga", "Germany", "League"))

conn.commit()
cur.close()
conn.close()
print("Reference data seeded.")
```

</details>

### 3. Pulling fixtures and stats

For club competitions (Bundesliga, Champions League, DFB-Pokal), each pull script fetches every Bayern fixture for that competition and season, along with Harry Kane's stats for any match he played. For international competitions (Nations League, Friendlies), the logic differs: a match is only inserted if Kane appears in that fixture's squad list, whether he played or was an unused substitute — club matches include every fixture regardless of his involvement, while international matches only include the ones he was actually part of. Each pull script also captures the logo and name of every team involved in a match, home and away, so that both Harry Kane's teams and their opponents are visually represented on the dashboard.

<details>
<summary><code>pull_bundesliga.py</code></summary>

```python
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

TEAM_ID = 157
PLAYER_ID = 184
LEAGUE_ID = 78
SEASON = 2024

response = requests.get(f"{BASE_URL}/fixtures", headers=headers, params={
    "team": TEAM_ID, "league": LEAGUE_ID, "season": SEASON
})
fixtures = response.json().get("response", [])
print(f"Found {len(fixtures)} fixtures.")

for fixture in fixtures:
    fid = fixture["fixture"]["id"]
    date = fixture["fixture"]["date"][:10]
    home = fixture["teams"]["home"]
    away = fixture["teams"]["away"]
    home_score = fixture["goals"]["home"]
    away_score = fixture["goals"]["away"]

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
            away_score = EXCLUDED.away_score,
            home_team_id = EXCLUDED.home_team_id,
            away_team_id = EXCLUDED.away_team_id
    """, (fid, date, LEAGUE_ID, f"{SEASON}/{SEASON+1}", TEAM_ID, home["name"], away["name"], home_score, away_score, home["id"], away["id"]))

    stats_response = requests.get(f"{BASE_URL}/fixtures/players", headers=headers, params={"fixture": fid})
    teams_data = stats_response.json().get("response", [])

    found_kane = False
    for team_block in teams_data:
        for player_entry in team_block.get("players", []):
            if player_entry["player"]["id"] == PLAYER_ID:
                found_kane = True
                stats = player_entry["statistics"][0]
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

                print(f"Match {fid} ({date}): Kane played, {minutes} mins, {goals} goals")

    if not found_kane:
        print(f"Match {fid} ({date}): no Kane data returned")

    conn.commit()
    time.sleep(7)

cur.close()
conn.close()
print("Done.")
```

</details>

<details>
<summary><code>pull_champions_league.py</code></summary>

```python
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

TEAM_ID = 157
PLAYER_ID = 184
LEAGUE_ID = 2
SEASON = 2024

response = requests.get(f"{BASE_URL}/fixtures", headers=headers, params={
    "team": TEAM_ID, "league": LEAGUE_ID, "season": SEASON
})
fixtures = response.json().get("response", [])
print(f"Found {len(fixtures)} fixtures.")

for fixture in fixtures:
    fid = fixture["fixture"]["id"]
    date = fixture["fixture"]["date"][:10]
    home = fixture["teams"]["home"]
    away = fixture["teams"]["away"]
    home_score = fixture["goals"]["home"]
    away_score = fixture["goals"]["away"]

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
    """, (fid, date, LEAGUE_ID, f"{SEASON}/{SEASON+1}", TEAM_ID, home["name"], away["name"], home_score, away_score, home["id"], away["id"]))

    stats_response = requests.get(f"{BASE_URL}/fixtures/players", headers=headers, params={"fixture": fid})
    teams_data = stats_response.json().get("response", [])

    found_kane = False
    for team_block in teams_data:
        for player_entry in team_block.get("players", []):
            if player_entry["player"]["id"] == PLAYER_ID:
                found_kane = True
                stats = player_entry["statistics"][0]
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

                print(f"Match {fid} ({date}): Kane played, {minutes} mins, {goals} goals")

    if not found_kane:
        print(f"Match {fid} ({date}): no Kane data returned")

    conn.commit()
    time.sleep(7)

cur.close()
conn.close()
print("Done.")
```

</details>

<details>
<summary><code>pull_dfb_pokal.py</code></summary>

```python
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

TEAM_ID = 157
PLAYER_ID = 184
LEAGUE_ID = 81
SEASON = 2024

response = requests.get(f"{BASE_URL}/fixtures", headers=headers, params={
    "team": TEAM_ID, "league": LEAGUE_ID, "season": SEASON
})
fixtures = response.json().get("response", [])
print(f"Found {len(fixtures)} fixtures.")

for fixture in fixtures:
    fid = fixture["fixture"]["id"]
    date = fixture["fixture"]["date"][:10]
    home = fixture["teams"]["home"]
    away = fixture["teams"]["away"]
    home_score = fixture["goals"]["home"]
    away_score = fixture["goals"]["away"]

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
    """, (fid, date, LEAGUE_ID, f"{SEASON}/{SEASON+1}", TEAM_ID, home["name"], away["name"], home_score, away_score, home["id"], away["id"]))

    stats_response = requests.get(f"{BASE_URL}/fixtures/players", headers=headers, params={"fixture": fid})
    teams_data = stats_response.json().get("response", [])

    found_kane = False
    for team_block in teams_data:
        for player_entry in team_block.get("players", []):
            if player_entry["player"]["id"] == PLAYER_ID:
                found_kane = True
                stats = player_entry["statistics"][0]
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

                print(f"Match {fid} ({date}): Kane played, {minutes} mins, {goals} goals")

    if not found_kane:
        print(f"Match {fid} ({date}): no Kane data returned")

    conn.commit()
    time.sleep(7)

cur.close()
conn.close()
print("Done.")
```

</details>

<details>
<summary><code>pull_international.py</code></summary>

```python
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
```

</details>

### Rate limiting

Since the free API tier is limited to 10 requests per minute, every pull script paces its requests with a 7-second delay between calls (`time.sleep(7)`), to avoid being rate-limited and ending up with silently incomplete data.

### Summary

Python was used to pull data from the API and load it into PostgreSQL on Neon, using the `requests` and `psycopg2` libraries. PostgreSQL was used to create tables and store data. Power BI was then used to do some light data cleaning via Power Query, create DAX measures, and build the report to showcase the results of this project.

---

## Data Cleaning & Transformation

### Key decisions

For this project I decided to go with a normalized schema instead of one flat table. This way I was able to separate the data across each table accordingly.

On every pull script I used `ON CONFLICT` so that it would be safe to re-run scripts without creating duplicates.

After pulling data for club and international opponents into the `teams` table, I verified that many had NULL values in the `country` column, because the `/fixtures` endpoint called in my Python script doesn't return country, only `id`, `name`, and `logo`. I solved that by creating `backfill_country.py`, which queried each affected team individually via the `/teams` endpoint to fill in the missing value.

I also noticed that the `players` table had no photo for Harry Kane, since the initial player lookup only captured his name, ID, and nationality. I created `update_images.py`, which queried the `/players/profiles` endpoint and used the returned `photo` field to populate `photo_url`.

While verifying how many matches Kane actually played, I noticed the percentage was far lower than expected for a season where he was an ever-present starter. This led me to discover that the free-tier rate limit was silently causing some requests to fail, resulting in missing data rather than an error.

To make the data more useful for analysis, I also transformed some of it beyond just storing what the API returned.

The API doesn't return continent for any team, only country. Since I wanted to group opponents by continent in the dashboard, I created `add_continent.py`, which mapped each existing country value to its continent using a manual dictionary, and added this as a new `continent` column in the `teams` table.

In my early pull scripts, the `matches` table only stored opponent names as plain text in the `home_team` and `away_team` columns, with no link back to the `teams` table. I transformed this into a proper relational structure by adding `home_team_id` and `away_team_id` columns, linking each match to the actual team record instead of just its name.

For international matches, I also applied a transformation at the logic level rather than the data level. Instead of inserting every England fixture the API returned, I only inserted a match if Harry Kane appeared in that fixture's squad list, whether he played or was an unused substitute. This reflects that a player must be called up before he even has the chance to play, so the `matches` table only includes games where he was genuinely part of the squad.

### Raw Table Creation

```sql
-- Teams
CREATE TABLE teams (
    team_id          INTEGER PRIMARY KEY,
    name             VARCHAR(100) NOT NULL,
    country          VARCHAR(50),
    logo_url         VARCHAR(255),
    continent        VARCHAR(20)
);

-- Competitions
CREATE TABLE competitions (
    competition_id   INTEGER PRIMARY KEY,
    name             VARCHAR(100) NOT NULL,
    country          VARCHAR(50),
    type             VARCHAR(20)
);

-- Players
CREATE TABLE players (
    player_id        INTEGER PRIMARY KEY,
    name             VARCHAR(100) NOT NULL,
    team_id          INTEGER REFERENCES teams(team_id),
    position         VARCHAR(20),
    nationality      VARCHAR(50),
    date_of_birth    DATE,
    photo_url        VARCHAR(255)
);

-- Matches
CREATE TABLE matches (
    match_id         INTEGER PRIMARY KEY,
    match_date       DATE NOT NULL,
    competition_id   INTEGER REFERENCES competitions(competition_id),
    season           VARCHAR(20),
    team_id          INTEGER REFERENCES teams(team_id),
    home_team        VARCHAR(100),
    away_team        VARCHAR(100),
    home_score       INTEGER,
    away_score       INTEGER,
    home_team_id     INTEGER REFERENCES teams(team_id),
    away_team_id     INTEGER REFERENCES teams(team_id)
);

-- Player match stats
CREATE TABLE player_match_stats (
    stat_id          SERIAL PRIMARY KEY,
    player_id        INTEGER REFERENCES players(player_id),
    match_id         INTEGER REFERENCES matches(match_id),
    minutes_played   INTEGER,
    goals            INTEGER DEFAULT 0,
    assists          INTEGER DEFAULT 0,
    shots_total      INTEGER DEFAULT 0,
    shots_on_target  INTEGER DEFAULT 0,
    yellow_cards     INTEGER DEFAULT 0,
    red_cards        INTEGER DEFAULT 0,
    rating           NUMERIC(3,1),
    pulled_at        TIMESTAMP DEFAULT NOW(),
    UNIQUE (player_id, match_id)
);
```

### Data Quality Checks (NULLs / duplicates)

```sql
-- Check for NULL country values in teams
SELECT team_id, name, country FROM teams WHERE country IS NULL;

-- Check for NULL team links in matches
SELECT match_id, home_team, away_team, home_team_id, away_team_id
FROM matches
WHERE home_team_id IS NULL;

-- Confirm no duplicate player/match stat rows exist
SELECT player_id, match_id, COUNT(*)
FROM player_match_stats
GROUP BY player_id, match_id
HAVING COUNT(*) > 1;

-- Verify matches played vs. possible, used to surface the rate-limit bug
SELECT
    COUNT(DISTINCT m.match_id) AS total_team_matches,
    COUNT(DISTINCT pms.match_id) AS matches_played,
    ROUND(COUNT(DISTINCT pms.match_id)::NUMERIC / COUNT(DISTINCT m.match_id) * 100, 1) AS pct_played
FROM matches m
LEFT JOIN player_match_stats pms 
    ON m.match_id = pms.match_id AND pms.player_id = 184;
```

### Clean Tables

<details>
<summary><code>backfill_country.py</code></summary>

```python
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
```

</details>

<details>
<summary><code>update_images.py</code></summary>

```python
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
```

</details>

<details>
<summary><code>add_continent.py</code></summary>

```python
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv("NEON_CONNECTION_STRING"))
cur = conn.cursor()

CONTINENT_MAP = {
    "Germany": "Europe", "England": "Europe", "Italy": "Europe",
    "Spain": "Europe", "Portugal": "Europe", "France": "Europe",
    "Netherlands": "Europe", "Ukraine": "Europe", "Croatia": "Europe",
    "Slovakia": "Europe", "Republic of Ireland": "Europe", "Ireland": "Europe",
    "Finland": "Europe", "Bosnia & Herzegovina": "Europe",
    "Bosnia and Herzegovina": "Europe", "Bosnia": "Europe", "Greece": "Europe",
    "Scotland": "Europe", "Belgium": "Europe", "Austria": "Europe",
    "Switzerland": "Europe", "Czech Republic": "Europe", "Poland": "Europe",
    "Denmark": "Europe", "Sweden": "Europe", "Norway": "Europe",
    "Hungary": "Europe", "Serbia": "Europe", "Turkey": "Europe",
    "Iceland": "Europe",
    "Argentina": "South America", "Brazil": "South America",
    "Uruguay": "South America", "Chile": "South America",
    "Colombia": "South America",
    "USA": "North America", "United States": "North America",
    "Mexico": "North America", "Canada": "North America",
    "Japan": "Asia", "South Korea": "Asia", "Saudi Arabia": "Asia",
    "Qatar": "Asia",
    "Morocco": "Africa", "Senegal": "Africa", "Nigeria": "Africa",
    "Egypt": "Africa",
    "Australia": "Oceania",
}

cur.execute("SELECT DISTINCT country FROM teams WHERE country IS NOT NULL")
countries = [row[0] for row in cur.fetchall()]

unmapped = []
for country in countries:
    continent = CONTINENT_MAP.get(country)
    if continent:
        cur.execute("UPDATE teams SET continent = %s WHERE country = %s", (continent, country))
        print(f"{country} -> {continent}")
    else:
        unmapped.append(country)

conn.commit()
cur.close()
conn.close()

if unmapped:
    print("\nNo mapping found for these — add them to CONTINENT_MAP:")
    for c in unmapped:
        print(f"  {c}")
else:
    print("\nAll countries mapped.")
```

</details>

### Final Table Structure

```sql
-- Teams
CREATE TABLE teams (
    team_id          INTEGER PRIMARY KEY,
    name             VARCHAR(100) NOT NULL,
    country          VARCHAR(50),
    logo_url         VARCHAR(255),
    continent        VARCHAR(20)
);

-- Competitions
CREATE TABLE competitions (
    competition_id   INTEGER PRIMARY KEY,
    name             VARCHAR(100) NOT NULL,
    country          VARCHAR(50),
    type             VARCHAR(20)
);

-- Players
CREATE TABLE players (
    player_id        INTEGER PRIMARY KEY,
    name             VARCHAR(100) NOT NULL,
    team_id          INTEGER REFERENCES teams(team_id),
    position         VARCHAR(20),
    nationality      VARCHAR(50),
    date_of_birth    DATE,
    photo_url        VARCHAR(255)
);

-- Matches
CREATE TABLE matches (
    match_id         INTEGER PRIMARY KEY,
    match_date       DATE NOT NULL,
    competition_id   INTEGER REFERENCES competitions(competition_id),
    season           VARCHAR(20),
    team_id          INTEGER REFERENCES teams(team_id),
    home_team        VARCHAR(100),
    away_team        VARCHAR(100),
    home_score       INTEGER,
    away_score       INTEGER,
    home_team_id     INTEGER REFERENCES teams(team_id),
    away_team_id     INTEGER REFERENCES teams(team_id)
);

-- Player match stats
CREATE TABLE player_match_stats (
    stat_id          SERIAL PRIMARY KEY,
    player_id        INTEGER REFERENCES players(player_id),
    match_id         INTEGER REFERENCES matches(match_id),
    minutes_played   INTEGER,
    goals            INTEGER DEFAULT 0,
    assists          INTEGER DEFAULT 0,
    shots_total      INTEGER DEFAULT 0,
    shots_on_target  INTEGER DEFAULT 0,
    yellow_cards     INTEGER DEFAULT 0,
    red_cards        INTEGER DEFAULT 0,
    rating           NUMERIC(3,1),
    pulled_at        TIMESTAMP DEFAULT NOW(),
    UNIQUE (player_id, match_id)
);
```

---

## Dashboard

### Power BI table modeling

To display both home and away team logos in the same visual, I duplicated the `teams` table in Power Query into two separate tables, `HomeTeams` and `AwayTeams`. Each was given its own active relationship to `matches` — `HomeTeams` linked via `home_team_id`, and `AwayTeams` linked via `away_team_id` — since Power BI only allows one active relationship between any two tables. This let both logo columns render correctly without conflicting with the original `teams` table, which remains linked via `team_id` for other parts of the model.

### DAX Measures

| Measure | Description |
|---|---|
| `G/A` | Combines goals and assists |
| `Cumulative G/A` | Running sum of G/A across the season, used to show form and progression |
| `G/A Per 90` | Normalizes goal involvement by playing time |
| `Shot Accuracy` | Percentage of total shots that were on target |
| `Shot Conversion` | Percentage of total shots that resulted in a goal |
| `Match Status` | Flags whether Kane featured in a given match, based on whether a stats row exists — used for conditional formatting on the match table |
| `Matches Played` | Count of distinct matches Kane actually appeared in |
| `Total Matches` | Count of total matches available — every team fixture for club competitions, or every match Kane was called up for internationally |
| `Matches Missed` | Gap between total possible matches and matches actually played |
| `% Played` | Matches played expressed as a percentage of total matches |

### Visuals

The dashboard includes:

- **Five KPI cards:** AMR (average match rating), G/A, G/A Per 90, Total Shots, Total Shots on Target
- **Two gauge visuals** showing Kane's Shot Accuracy and Shot Conversion
- **Two donut charts:** "Goals by Competition" and "Assists by Competition," showing Harry Kane's performance by each competition
- **A stacked bar chart:** "Matches Played Vs. Matches Missed by Competition," comparing matches played to matches missed and total matches between competitions, with % Played available on hover via tooltip
- **A line chart:** "Cumulative G/A Across the Season," visualizing form and progression over time
- **A detailed match-by-match table** with competition, date, home and away teams with their logos, match result, and Harry Kane's stats for each match
- **A summary table** breaking down stats by competition
- **Competition and date range slicers**, filtering across all visuals

![Dashboard overview](assets/dashboard-full.png)

---

## Key Findings

Harry Kane recorded **53 goal involvements** (42 goals, 11 assists) across the 2024/2025 season, maintaining an **average match rating of 7.63**. He also had a 1.19 goal involvement per 90 minutes, showing strong and consistent involvement across all matches.

Kane had a **61.18% shot accuracy** across all competitions, meaning more than half his shots hit the target. His **shot conversion** sits lower, at **27.63%**, showing that while most of his shots test the goalkeeper, a smaller share of them actually result in a goal — a normal gap for a striker, but a useful distinction between shot precision and finishing output.

Of his 42 goals, **26 came in the Bundesliga** and **11 in the UEFA Champions League**. Of his 11 assists, **8 came in the Bundesliga** and **2 in the UEFA Champions League**.

Most of his matches were played in the **Bundesliga**, where he participated in **91.18%** of them (31 out of 34 possible). Right after were the **UEFA Champions League** games, with **92.86%** participation (13/14). He also played in **5 out of 5** possible matches for the UEFA Nations League, **2 out of 3** for the DFB Pokal, and **2 out of 2** national team Friendlies.

By looking at the "Cumulative G/A Across the Season" graph, we can see that he had an early-season slow start, followed by a strong second half.

By analyzing the match-by-match table, he had **2 matches with a 10.0 rating**: one against Dinamo Zagreb, where he scored 4 goals, and another against Holstein Kiel, where he scored 3 goals and assisted 1.

He didn't have many cards, with only **7 yellow cards** and **0 red cards** in this season.

In terms of his performance for the England national team, the international calendar meant far fewer matches than at club level, but he still contributed **4 goals** across those appearances (3 in the UEFA Nations League, 1 in Friendlies), with 0 assists, from 5 Nations League and 2 Friendlies matches.

> **Note:** DFB-Pokal figures above should be re-verified after the `pull_dfb_pokal.py` fix (`LEAGUE_ID` corrected to `81`) is re-run.

---

## Limitations

Since I don't have access to the paid version of API-FOOTBALL, I was only able to access data up to and including the 2024/2025 season. My first plan was to build this project around the current 2026/2027 season, where it would update automatically every week with Harry Kane's matches. Due to this limitation, the project instead uses a completed, static season, so the dashboard reflects a finished story rather than one that updates over time.

The free tier is also limited to 10 requests per minute. This required pacing every pull script with a delay between calls, which significantly slowed down the data collection process, especially across five different competitions.

Since this project was ultimately built around a completed, static season rather than the live 2026/2027 season originally planned, the GitHub Actions scheduling and automatic weekly refresh were never implemented. The pipeline runs manually, rather than on a recurring schedule, as it would need to for a live-tracking version of this project.

The `continent` column in the `teams` table relies on a manually built mapping dictionary, covering only the countries that appear in this dataset. It isn't an automatic or universal solution, and would need to be extended by hand for any new country not already included.

The squad-presence logic used for international matches, where a match is only inserted if Harry Kane appears in that fixture's player list, depends entirely on API-Football's own data being complete and accurate. If the API has incomplete squad data for a given match, that match could be missed or misrepresented in this dataset.

Finally, this project was built and populated specifically for Harry Kane. While the schema is structured to support any player, extending it to track others would require running the pipeline again for each additional player.
