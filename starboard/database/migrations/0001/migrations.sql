ALTER TABLE starboards ADD COLUMN replied_to BOOLEAN;
UPDATE starboards SET replied_to = true;
ALTER TABLE starboards ALTER COLUMN replied_to SET NOT NULL;