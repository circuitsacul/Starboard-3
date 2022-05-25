ALTER TABLE starboards ADD COLUMN autoreact_upvote BOOLEAN;
ALTER TABLE starboards ADD COLUMN autoreact_downvote BOOLEAN;
ALTER TABLE starboards DROP COLUMN autoreact;
UPDATE starboards SET autoreact_upvote = true, autoreact_downvote = true;
ALTER TABLE starboards ALTER COLUMN autoreact_upvote SET NOT NULL;
ALTER TABLE starboards ALTER COLUMN autoreact_downvote SET NOT NULL;