ALTER TABLE apps RENAME TO sofa_manifests;

ALTER TABLE sofa_manifests ADD COLUMN payment_address TEXT;

CREATE TABLE IF NOT EXISTS apps (
    token_id TEXT PRIMARY KEY,
    name TEXT,
    description TEXT,
    reputation_score DECIMAL,
    review_count INT,
    featured BOOLEAN DEFAULT FALSE,
    created TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc'),
    updated TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc')
);

INSERT INTO apps (token_id, name, description, reputation_score, review_count, featured, created, updated)
    (SELECT eth_address, display_name, '', NULL, 0, featured, created, updated FROM sofa_manifests);

ALTER TABLE sofa_manifests DROP COLUMN featured;
ALTER TABLE sofa_manifests DROP COLUMN display_name;

ALTER TABLE sofa_manifests RENAME COLUMN eth_address TO token_id;

ALTER TABLE submissions RENAME COLUMN app_eth_address TO app_token_id;
ALTER TABLE submissions RENAME COLUMN submitter_address TO submitter_token_id;

ALTER TABLE admins RENAME COLUMN eth_address TO token_id;
