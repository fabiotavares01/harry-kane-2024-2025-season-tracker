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
