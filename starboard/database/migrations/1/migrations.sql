ALTER TABLE posroles ADD COLUMN max_members INTEGER;
ALTER TABLE posroles DROP COLUMN max_users;
ALTER TABLE posroles ALTER COLUMN max_members SET NOT NULL;