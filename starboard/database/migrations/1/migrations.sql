ALTER TABLE posrole_members DROP CONSTRAINT role_id_fk;
ALTER TABLE posrole_members DROP CONSTRAINT user_id_fk;
ALTER TABLE posroles DROP CONSTRAINT guild_id_fk;
DROP TABLE posrole_members;
DROP TABLE posroles;