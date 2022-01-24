ALTER TABLE starboards ADD COLUMN webhook_id NUMERIC;
ALTER TABLE starboards DROP COLUMN webhook_url;