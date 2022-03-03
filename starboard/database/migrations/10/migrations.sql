ALTER TABLE users ADD COLUMN donated_cents BIGINT;
UPDATE users SET donated_cents=0;
ALTER TABLE users ALTER COLUMN donated_cents SET NOT NULL;