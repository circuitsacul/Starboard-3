ALTER TABLE autoredeems DROP CONSTRAINT guildid_fk;
ALTER TABLE autoredeems DROP CONSTRAINT userid_fk;
DROP TABLE autoredeems;
ALTER TABLE members ADD COLUMN autoredeem_enabled BOOLEAN;
UPDATE members SET autoredeem_enabled=false;
ALTER TABLE members ALTER COLUMN autoredeem_enabled SET NOT NULL;