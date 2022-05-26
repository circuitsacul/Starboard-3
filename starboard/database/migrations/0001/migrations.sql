ALTER TABLE starboards ADD COLUMN older_than BIGINT;
ALTER TABLE starboards ADD COLUMN newer_than BIGINT;
UPDATE starboards SET older_than = 0, newer_than = 0;
ALTER TABLE starboards ALTER COLUMN older_than SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN newer_than SET NOT NULL;