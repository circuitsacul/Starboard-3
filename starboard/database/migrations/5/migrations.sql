ALTER TABLE members ADD COLUMN xp_given INTEGER;
UPDATE members SET xp_given=0;
ALTER TABLE guilds DROP COLUMN lvl_channel_id;
ALTER TABLE guilds DROP COLUMN ping_on_lvlup;
ALTER TABLE members DROP COLUMN stars_given;
ALTER TABLE members DROP COLUMN stars_received;
ALTER TABLE members DROP COLUMN level;
ALTER TABLE users DROP COLUMN locale;
ALTER TABLE users DROP COLUMN public;
ALTER TABLE members ALTER COLUMN xp_given SET NOT NULL;