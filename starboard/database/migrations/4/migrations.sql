ALTER TABLE starboards ADD COLUMN use_server_profile BOOLEAN;
UPDATE starboards SET use_server_profile = true;
ALTER TABLE starboards DROP COLUMN use_nicknames;
ALTER TABLE starboards ALTER COLUMN use_server_profile SET NOT NULL;