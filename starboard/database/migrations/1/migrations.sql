ALTER TABLE starboards ADD COLUMN enabled BOOLEAN;
ALTER TABLE starboards DROP COLUMN locked;
ALTER TABLE starboards DROP COLUMN channel_bl;
ALTER TABLE starboards DROP COLUMN channel_wl;
ALTER TABLE starboards ALTER COLUMN enabled SET NOT NULL;