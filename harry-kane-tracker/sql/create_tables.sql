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
