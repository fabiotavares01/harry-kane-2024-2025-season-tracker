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
