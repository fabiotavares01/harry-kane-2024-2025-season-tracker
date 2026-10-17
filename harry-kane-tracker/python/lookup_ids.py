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
