CREATE TABLE IF NOT EXISTS submissions (
    app_eth_address TEXT,
    submitter_address TEXT,
    request_for_featured BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (app_eth_address, submitter_address)
);

ALTER TABLE apps ADD PRIMARY KEY (eth_address);
