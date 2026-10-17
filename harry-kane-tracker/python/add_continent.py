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
