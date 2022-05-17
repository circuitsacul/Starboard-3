CREATE TABLE patrons ();
ALTER TABLE patrons ADD COLUMN patreon_id VARCHAR(64);
ALTER TABLE patrons ADD COLUMN discord_id NUMERIC;
ALTER TABLE patrons ADD COLUMN last_patreon_total_cents BIGINT;
ALTER TABLE users DROP COLUMN last_patreon_total_cents;
ALTER TABLE patrons ALTER COLUMN patreon_id SET NOT NULL;
ALTER TABLE patrons ALTER COLUMN last_patreon_total_cents SET NOT NULL;
CREATE INDEX _hash_index_patrons__discord_id ON patrons USING HASH ( ( discord_id ) );
ALTER TABLE patrons ADD CONSTRAINT _patrons_patreon_id_primary_key PRIMARY KEY ( patreon_id );