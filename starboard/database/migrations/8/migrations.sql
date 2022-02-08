ALTER TABLE permgroups DROP CONSTRAINT guild_id_fk;
ALTER TABLE permroles DROP CONSTRAINT pgid_fk;
DROP TABLE permgroups;
DROP TABLE permroles;
ALTER TABLE starboards DROP COLUMN channel_bl;
ALTER TABLE starboards DROP COLUMN channel_wl;