CREATE TABLE IF NOT EXISTS apps (
    token_id TEXT PRIMARY KEY,
    name TEXT,
    description TEXT,
    reputation_score DECIMAL,
    review_count INT DEFAULT 0,
    featured BOOLEAN DEFAULT FALSE,
    created TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc'),
    updated TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc')
);

CREATE TABLE IF NOT EXISTS sofa_manifests (
    token_id TEXT PRIMARY KEY,
    payment_address TEXT,
    username TEXT UNIQUE,
    protocol TEXT,
    avatar_url TEXT,
    web_app TEXT,
    interfaces TEXT[],
    languages TEXT[],
    init_request TEXT[]
);

CREATE TABLE IF NOT EXISTS submissions (
    app_token_id TEXT,
    submitter_token_id TEXT,
    request_for_featured BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (app_token_id, submitter_token_id)
);

CREATE TABLE IF NOT EXISTS admins (
    token_id TEXT PRIMARY KEY
);

UPDATE database_version SET version_number = 5;
