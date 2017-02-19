CREATE TABLE IF NOT EXISTS apps (
    eth_address TEXT UNIQUE,
    username TEXT UNIQUE,
    display_name TEXT,
    protocol TEXT,
    avatar_url TEXT,
    web_app TEXT,
    interfaces TEXT[],
    languages TEXT[],
    init_request TEXT[],
    featured BOOLEAN DEFAULT FALSE,
    created TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc'),
    updated TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc')
);

UPDATE database_version SET version_number = 1;
