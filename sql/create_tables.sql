CREATE TABLE IF NOT EXISTS apps (
    eth_address TEXT PRIMARY KEY,
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

CREATE TABLE IF NOT EXISTS submissions (
    app_eth_address TEXT,
    submitter_address TEXT,
    request_for_featured BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (app_eth_address, submitter_address)
);

CREATE TABLE IF NOT EXISTS admins (
    eth_address TEXT PRIMARY KEY
);

UPDATE database_version SET version_number = 3;
