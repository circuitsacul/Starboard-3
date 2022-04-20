ALTER TABLE starboards ADD COLUMN jump_to_message BOOLEAN;
ALTER TABLE starboards ADD COLUMN attachments_list BOOLEAN;
UPDATE starboards SET jump_to_message = true, attachments_list = true;
ALTER TABLE starboards ALTER COLUMN jump_to_message SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN attachments_list SET NOT NULL;