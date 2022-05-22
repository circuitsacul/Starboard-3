ALTER TABLE starboards ADD COLUMN xp_multiplier REAL;
ALTER TABLE starboards DROP COLUMN disable_xp;
ALTER TABLE starboards ALTER COLUMN xp_multiplier SET NOT NULL;
ALTER TABLE members ALTER COLUMN xp TYPE REAL USING xp::real;
DROP INDEX _btree_index_stars__message_id_starboard_id;
CREATE INDEX _hash_index_stars__starboard_id ON stars USING HASH ( ( starboard_id ) );
CREATE INDEX _hash_index_stars__user_id ON stars USING HASH ( ( user_id ) );
CREATE INDEX _hash_index_stars__message_id ON stars USING HASH ( ( message_id ) );