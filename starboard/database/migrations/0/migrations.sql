CREATE TABLE _migrations ();
CREATE TABLE aschannels ();
CREATE TABLE autoredeems ();
CREATE TABLE guilds ();
CREATE TABLE members ();
CREATE TABLE messages ();
CREATE TABLE permgroups ();
CREATE TABLE permroles ();
CREATE TABLE posrole_members ();
CREATE TABLE posroles ();
CREATE TABLE sb_messages ();
CREATE TABLE starboards ();
CREATE TABLE stars ();
CREATE TABLE users ();
CREATE TABLE xproles ();
ALTER TABLE _migrations ADD COLUMN id_ INTEGER;
ALTER TABLE aschannels ADD COLUMN delete_invalid BOOLEAN;
ALTER TABLE aschannels ADD COLUMN emojis TEXT[];
ALTER TABLE aschannels ADD COLUMN exclude_regex VARCHAR(512);
ALTER TABLE aschannels ADD COLUMN guild_id NUMERIC;
ALTER TABLE aschannels ADD COLUMN id NUMERIC;
ALTER TABLE aschannels ADD COLUMN max_chars SMALLINT;
ALTER TABLE aschannels ADD COLUMN min_chars SMALLINT;
ALTER TABLE aschannels ADD COLUMN regex VARCHAR(512);
ALTER TABLE aschannels ADD COLUMN require_image BOOLEAN;
ALTER TABLE autoredeems ADD COLUMN enabled_on TIMESTAMP;
ALTER TABLE autoredeems ADD COLUMN guild_id NUMERIC;
ALTER TABLE autoredeems ADD COLUMN user_id NUMERIC;
ALTER TABLE guilds ADD COLUMN enable_xp_cooldown BOOLEAN;
ALTER TABLE guilds ADD COLUMN id NUMERIC;
ALTER TABLE guilds ADD COLUMN locale VARCHAR(8);
ALTER TABLE guilds ADD COLUMN log_channel_id NUMERIC;
ALTER TABLE guilds ADD COLUMN lvl_channel_id NUMERIC;
ALTER TABLE guilds ADD COLUMN ping_on_lvlup BOOLEAN;
ALTER TABLE guilds ADD COLUMN premium_end TIMESTAMP;
ALTER TABLE guilds ADD COLUMN stack_posroles BOOLEAN;
ALTER TABLE guilds ADD COLUMN stack_xproles BOOLEAN;
ALTER TABLE guilds ADD COLUMN xp_cooldown_bucket SMALLINT;
ALTER TABLE guilds ADD COLUMN xp_cooldown_count SMALLINT;
ALTER TABLE members ADD COLUMN guild_id NUMERIC;
ALTER TABLE members ADD COLUMN level SMALLINT;
ALTER TABLE members ADD COLUMN stars_given INTEGER;
ALTER TABLE members ADD COLUMN stars_received INTEGER;
ALTER TABLE members ADD COLUMN user_id NUMERIC;
ALTER TABLE members ADD COLUMN xp INTEGER;
ALTER TABLE messages ADD COLUMN author_id NUMERIC;
ALTER TABLE messages ADD COLUMN channel_id NUMERIC;
ALTER TABLE messages ADD COLUMN forced_to NUMERIC[];
ALTER TABLE messages ADD COLUMN frozen BOOLEAN;
ALTER TABLE messages ADD COLUMN guild_id NUMERIC;
ALTER TABLE messages ADD COLUMN id NUMERIC;
ALTER TABLE messages ADD COLUMN is_nsfw BOOLEAN;
ALTER TABLE messages ADD COLUMN trash_reason VARCHAR(512);
ALTER TABLE messages ADD COLUMN trashed BOOLEAN;
ALTER TABLE permgroups ADD COLUMN channels NUMERIC[];
ALTER TABLE permgroups ADD COLUMN guild_id NUMERIC;
ALTER TABLE permgroups ADD COLUMN id SERIAL;
ALTER TABLE permgroups ADD COLUMN index SMALLINT;
ALTER TABLE permgroups ADD COLUMN name TEXT;
ALTER TABLE permgroups ADD COLUMN starboards NUMERIC[];
ALTER TABLE permroles ADD COLUMN allow_commands BOOLEAN;
ALTER TABLE permroles ADD COLUMN gain_xp BOOLEAN;
ALTER TABLE permroles ADD COLUMN give_stars BOOLEAN;
ALTER TABLE permroles ADD COLUMN index SMALLINT;
ALTER TABLE permroles ADD COLUMN on_starboard BOOLEAN;
ALTER TABLE permroles ADD COLUMN permgroup_id INTEGER;
ALTER TABLE permroles ADD COLUMN pos_roles BOOLEAN;
ALTER TABLE permroles ADD COLUMN role_id NUMERIC;
ALTER TABLE permroles ADD COLUMN xp_roles BOOLEAN;
ALTER TABLE posrole_members ADD COLUMN role_id NUMERIC;
ALTER TABLE posrole_members ADD COLUMN user_id NUMERIC;
ALTER TABLE posroles ADD COLUMN guild_id NUMERIC;
ALTER TABLE posroles ADD COLUMN id NUMERIC;
ALTER TABLE posroles ADD COLUMN max_users NUMERIC;
ALTER TABLE sb_messages ADD COLUMN last_known_star_count SMALLINT;
ALTER TABLE sb_messages ADD COLUMN message_id NUMERIC;
ALTER TABLE sb_messages ADD COLUMN sb_message_id NUMERIC;
ALTER TABLE sb_messages ADD COLUMN starboard_id NUMERIC;
ALTER TABLE starboards ADD COLUMN allow_bots BOOLEAN;
ALTER TABLE starboards ADD COLUMN allow_explore BOOLEAN;
ALTER TABLE starboards ADD COLUMN autoreact BOOLEAN;
ALTER TABLE starboards ADD COLUMN channel_bl NUMERIC[];
ALTER TABLE starboards ADD COLUMN channel_wl NUMERIC[];
ALTER TABLE starboards ADD COLUMN color INTEGER;
ALTER TABLE starboards ADD COLUMN disable_xp BOOLEAN;
ALTER TABLE starboards ADD COLUMN display_emoji TEXT;
ALTER TABLE starboards ADD COLUMN exclude_regex TEXT;
ALTER TABLE starboards ADD COLUMN guild_id NUMERIC;
ALTER TABLE starboards ADD COLUMN id NUMERIC;
ALTER TABLE starboards ADD COLUMN images_only BOOLEAN;
ALTER TABLE starboards ADD COLUMN link_deletes BOOLEAN;
ALTER TABLE starboards ADD COLUMN link_edits BOOLEAN;
ALTER TABLE starboards ADD COLUMN locked BOOLEAN;
ALTER TABLE starboards ADD COLUMN ping_author BOOLEAN;
ALTER TABLE starboards ADD COLUMN regex TEXT;
ALTER TABLE starboards ADD COLUMN remove_invalid BOOLEAN;
ALTER TABLE starboards ADD COLUMN required SMALLINT;
ALTER TABLE starboards ADD COLUMN required_remove SMALLINT;
ALTER TABLE starboards ADD COLUMN self_star BOOLEAN;
ALTER TABLE starboards ADD COLUMN star_emojis TEXT[];
ALTER TABLE starboards ADD COLUMN use_nicknames BOOLEAN;
ALTER TABLE starboards ADD COLUMN use_webhook BOOLEAN;
ALTER TABLE starboards ADD COLUMN webhook_avatar TEXT;
ALTER TABLE starboards ADD COLUMN webhook_name TEXT;
ALTER TABLE starboards ADD COLUMN webhook_url TEXT;
ALTER TABLE stars ADD COLUMN message_id NUMERIC;
ALTER TABLE stars ADD COLUMN starboard_id NUMERIC;
ALTER TABLE stars ADD COLUMN user_id NUMERIC;
ALTER TABLE users ADD COLUMN credits INTEGER;
ALTER TABLE users ADD COLUMN id NUMERIC;
ALTER TABLE users ADD COLUMN last_patreon_total MONEY;
ALTER TABLE users ADD COLUMN locale VARCHAR(16);
ALTER TABLE users ADD COLUMN patreon_status SMALLINT;
ALTER TABLE users ADD COLUMN public BOOLEAN;
ALTER TABLE users ADD COLUMN total_donated MONEY;
ALTER TABLE users ADD COLUMN votes INTEGER;
ALTER TABLE xproles ADD COLUMN guild_id NUMERIC;
ALTER TABLE xproles ADD COLUMN id NUMERIC;
ALTER TABLE xproles ADD COLUMN required SMALLINT;
ALTER TABLE _migrations ALTER COLUMN id_ SET NOT NULL;
ALTER TABLE aschannels ALTER COLUMN delete_invalid SET NOT NULL;
ALTER TABLE aschannels ALTER COLUMN emojis SET NOT NULL;
ALTER TABLE aschannels ALTER COLUMN exclude_regex SET NOT NULL;
ALTER TABLE aschannels ALTER COLUMN guild_id SET NOT NULL;
ALTER TABLE aschannels ALTER COLUMN id SET NOT NULL;
ALTER TABLE aschannels ALTER COLUMN min_chars SET NOT NULL;
ALTER TABLE aschannels ALTER COLUMN regex SET NOT NULL;
ALTER TABLE aschannels ALTER COLUMN require_image SET NOT NULL;
ALTER TABLE autoredeems ALTER COLUMN enabled_on SET NOT NULL;
ALTER TABLE autoredeems ALTER COLUMN guild_id SET NOT NULL;
ALTER TABLE autoredeems ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE guilds ALTER COLUMN enable_xp_cooldown SET NOT NULL;
ALTER TABLE guilds ALTER COLUMN id SET NOT NULL;
ALTER TABLE guilds ALTER COLUMN locale SET NOT NULL;
ALTER TABLE guilds ALTER COLUMN ping_on_lvlup SET NOT NULL;
ALTER TABLE guilds ALTER COLUMN stack_posroles SET NOT NULL;
ALTER TABLE guilds ALTER COLUMN stack_xproles SET NOT NULL;
ALTER TABLE guilds ALTER COLUMN xp_cooldown_bucket SET NOT NULL;
ALTER TABLE guilds ALTER COLUMN xp_cooldown_count SET NOT NULL;
ALTER TABLE members ALTER COLUMN guild_id SET NOT NULL;
ALTER TABLE members ALTER COLUMN level SET NOT NULL;
ALTER TABLE members ALTER COLUMN stars_given SET NOT NULL;
ALTER TABLE members ALTER COLUMN stars_received SET NOT NULL;
ALTER TABLE members ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE members ALTER COLUMN xp SET NOT NULL;
ALTER TABLE messages ALTER COLUMN author_id SET NOT NULL;
ALTER TABLE messages ALTER COLUMN channel_id SET NOT NULL;
ALTER TABLE messages ALTER COLUMN forced_to SET NOT NULL;
ALTER TABLE messages ALTER COLUMN frozen SET NOT NULL;
ALTER TABLE messages ALTER COLUMN guild_id SET NOT NULL;
ALTER TABLE messages ALTER COLUMN id SET NOT NULL;
ALTER TABLE messages ALTER COLUMN is_nsfw SET NOT NULL;
ALTER TABLE messages ALTER COLUMN trashed SET NOT NULL;
ALTER TABLE permgroups ALTER COLUMN channels SET NOT NULL;
ALTER TABLE permgroups ALTER COLUMN guild_id SET NOT NULL;
ALTER TABLE permgroups ALTER COLUMN id SET NOT NULL;
ALTER TABLE permgroups ALTER COLUMN index SET NOT NULL;
ALTER TABLE permgroups ALTER COLUMN name SET NOT NULL;
ALTER TABLE permgroups ALTER COLUMN starboards SET NOT NULL;
ALTER TABLE permroles ALTER COLUMN index SET NOT NULL;
ALTER TABLE permroles ALTER COLUMN permgroup_id SET NOT NULL;
ALTER TABLE permroles ALTER COLUMN role_id SET NOT NULL;
ALTER TABLE posrole_members ALTER COLUMN role_id SET NOT NULL;
ALTER TABLE posrole_members ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE posroles ALTER COLUMN guild_id SET NOT NULL;
ALTER TABLE posroles ALTER COLUMN id SET NOT NULL;
ALTER TABLE posroles ALTER COLUMN max_users SET NOT NULL;
ALTER TABLE sb_messages ALTER COLUMN last_known_star_count SET NOT NULL;
ALTER TABLE sb_messages ALTER COLUMN message_id SET NOT NULL;
ALTER TABLE sb_messages ALTER COLUMN starboard_id SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN allow_bots SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN allow_explore SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN autoreact SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN channel_bl SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN channel_wl SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN disable_xp SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN exclude_regex SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN guild_id SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN id SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN images_only SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN link_deletes SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN link_edits SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN locked SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN ping_author SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN regex SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN remove_invalid SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN required SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN required_remove SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN self_star SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN star_emojis SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN use_nicknames SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN use_webhook SET NOT NULL;
ALTER TABLE stars ALTER COLUMN message_id SET NOT NULL;
ALTER TABLE stars ALTER COLUMN starboard_id SET NOT NULL;
ALTER TABLE stars ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE users ALTER COLUMN credits SET NOT NULL;
ALTER TABLE users ALTER COLUMN id SET NOT NULL;
ALTER TABLE users ALTER COLUMN last_patreon_total SET NOT NULL;
ALTER TABLE users ALTER COLUMN locale SET NOT NULL;
ALTER TABLE users ALTER COLUMN patreon_status SET NOT NULL;
ALTER TABLE users ALTER COLUMN public SET NOT NULL;
ALTER TABLE users ALTER COLUMN total_donated SET NOT NULL;
ALTER TABLE users ALTER COLUMN votes SET NOT NULL;
ALTER TABLE xproles ALTER COLUMN guild_id SET NOT NULL;
ALTER TABLE xproles ALTER COLUMN id SET NOT NULL;
ALTER TABLE xproles ALTER COLUMN required SET NOT NULL;
ALTER TABLE sb_messages ADD CONSTRAINT sb_message_id_unique UNIQUE ( sb_message_id );
ALTER TABLE _migrations ADD CONSTRAINT __migrations_id__primary_key PRIMARY KEY ( id_ );
ALTER TABLE aschannels ADD CONSTRAINT _aschannels_id_primary_key PRIMARY KEY ( id );
ALTER TABLE autoredeems ADD CONSTRAINT _autoredeems_user_id_guild_id_primary_key PRIMARY KEY ( user_id , guild_id );
ALTER TABLE guilds ADD CONSTRAINT _guilds_id_primary_key PRIMARY KEY ( id );
ALTER TABLE members ADD CONSTRAINT _members_user_id_guild_id_primary_key PRIMARY KEY ( user_id , guild_id );
ALTER TABLE messages ADD CONSTRAINT _messages_id_primary_key PRIMARY KEY ( id );
ALTER TABLE permgroups ADD CONSTRAINT _permgroups_id_primary_key PRIMARY KEY ( id );
ALTER TABLE permroles ADD CONSTRAINT _permroles_permgroup_id_role_id_primary_key PRIMARY KEY ( permgroup_id , role_id );
ALTER TABLE posrole_members ADD CONSTRAINT _posrole_members_role_id_user_id_primary_key PRIMARY KEY ( role_id , user_id );
ALTER TABLE posroles ADD CONSTRAINT _posroles_id_primary_key PRIMARY KEY ( id );
ALTER TABLE sb_messages ADD CONSTRAINT _sb_messages_message_id_starboard_id_primary_key PRIMARY KEY ( message_id , starboard_id );
ALTER TABLE starboards ADD CONSTRAINT _starboards_id_primary_key PRIMARY KEY ( id );
ALTER TABLE stars ADD CONSTRAINT _stars_message_id_starboard_id_user_id_primary_key PRIMARY KEY ( message_id , starboard_id , user_id );
ALTER TABLE users ADD CONSTRAINT _users_id_primary_key PRIMARY KEY ( id );
ALTER TABLE xproles ADD CONSTRAINT _xproles_id_primary_key PRIMARY KEY ( id );
ALTER TABLE aschannels ADD CONSTRAINT guild_id_fk FOREIGN KEY ( guild_id ) REFERENCES guilds ( id ) MATCH SIMPLE ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE autoredeems ADD CONSTRAINT guildid_fk FOREIGN KEY ( guild_id ) REFERENCES guilds ( id ) MATCH SIMPLE ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE autoredeems ADD CONSTRAINT userid_fk FOREIGN KEY ( user_id ) REFERENCES users ( id ) MATCH SIMPLE ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE members ADD CONSTRAINT guildid_fk FOREIGN KEY ( guild_id ) REFERENCES guilds ( id ) MATCH SIMPLE ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE members ADD CONSTRAINT userid_fk FOREIGN KEY ( user_id ) REFERENCES users ( id ) MATCH SIMPLE ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE messages ADD CONSTRAINT author_id_fk FOREIGN KEY ( author_id ) REFERENCES users ( id ) MATCH SIMPLE ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE messages ADD CONSTRAINT guild_id_fk FOREIGN KEY ( guild_id ) REFERENCES guilds ( id ) MATCH SIMPLE ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE permgroups ADD CONSTRAINT guild_id_fk FOREIGN KEY ( guild_id ) REFERENCES guilds ( id ) MATCH SIMPLE ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE permroles ADD CONSTRAINT pgid_fk FOREIGN KEY ( permgroup_id ) REFERENCES permgroups ( id ) MATCH SIMPLE ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE posrole_members ADD CONSTRAINT role_id_fk FOREIGN KEY ( role_id ) REFERENCES posroles ( id ) MATCH SIMPLE ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE posrole_members ADD CONSTRAINT user_id_fk FOREIGN KEY ( user_id ) REFERENCES users ( id ) MATCH SIMPLE ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE posroles ADD CONSTRAINT guild_id_fk FOREIGN KEY ( guild_id ) REFERENCES guilds ( id ) MATCH SIMPLE ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE sb_messages ADD CONSTRAINT message_id_fk FOREIGN KEY ( message_id ) REFERENCES messages ( id ) MATCH SIMPLE ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE sb_messages ADD CONSTRAINT starboard_id_fk FOREIGN KEY ( starboard_id ) REFERENCES starboards ( id ) MATCH SIMPLE ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE starboards ADD CONSTRAINT guild_id_fk FOREIGN KEY ( guild_id ) REFERENCES guilds ( id ) MATCH SIMPLE ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE stars ADD CONSTRAINT message_id_fk FOREIGN KEY ( message_id ) REFERENCES messages ( id ) MATCH SIMPLE ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE stars ADD CONSTRAINT starboard_id_fk FOREIGN KEY ( starboard_id ) REFERENCES starboards ( id ) MATCH SIMPLE ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE stars ADD CONSTRAINT user_id_fk FOREIGN KEY ( user_id ) REFERENCES users ( id ) MATCH SIMPLE ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE xproles ADD CONSTRAINT guild_id_fk FOREIGN KEY ( guild_id ) REFERENCES guilds ( id ) MATCH SIMPLE ON DELETE CASCADE ON UPDATE CASCADE;