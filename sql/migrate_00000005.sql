ALTER TABLE apps ALTER COLUMN review_count SET DEFAULT 0;

UPDATE apps SET review_count = 0 WHERE review_count is NULL;
