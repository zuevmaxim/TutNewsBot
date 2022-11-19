BEGIN;

CREATE TABLE Channel
(
    id   SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE
);

CREATE TABLE Post
(
    id         SERIAL PRIMARY KEY,
    post_id    INT                         NOT NULL,
    channel_id INT REFERENCES Channel (id) NOT NULL,
    timestamp  TIMESTAMPTZ                 NOT NULL,
    comments   INT                         NOT NULL DEFAULT 0 CHECK (comments >= 0),
    reactions  INT                         NOT NULL DEFAULT 0 CHECK (reactions >= 0),

    UNIQUE (post_id, channel_id)
);

CREATE TABLE BotUser
(
    id      SERIAL PRIMARY KEY,
    user_id INT     NOT NULL UNIQUE,
    lang    VARCHAR NOT NULL
);

CREATE TABLE Subscription
(
    id                SERIAL PRIMARY KEY,
    user_id           INT REFERENCES BotUser (id) NOT NULL,
    channel_id        INT REFERENCES Channel (id) NOT NULL,
    percentile        INT                         NOT NULL CHECK (0 <= percentile AND percentile <= 100),
    last_seen_post_id INT                         NOT NULL DEFAULT -1,

    UNIQUE (user_id, channel_id)
);

CREATE TABLE Statistics
(
    id         SERIAL PRIMARY KEY,
    channel_id INT REFERENCES Channel (id) NOT NULL,
    percentile INT                         NOT NULL CHECK (0 <= percentile AND percentile <= 100),
    comments   INT                         NOT NULL DEFAULT 0 CHECK (comments >= 0),
    reactions  INT                         NOT NULL DEFAULT 0 CHECK (reactions >= 0),

    UNIQUE (channel_id, percentile)
);

COMMIT;