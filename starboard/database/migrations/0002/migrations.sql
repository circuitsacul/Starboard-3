ALTER TABLE starboards ADD COLUMN prem_locked BOOLEAN;
ALTER TABLE aschannels ADD COLUMN prem_locked BOOLEAN;
UPDATE starboards SET prem_locked = false;
UPDATE aschannels SET prem_locked = false;
ALTER TABLE starboards ALTER COLUMN prem_locked SET NOT NULL;
ALTER TABLE aschannels ALTER COLUMN prem_locked SET NOT NULL;