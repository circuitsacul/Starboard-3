ALTER TABLE starboards ADD COLUMN extra_embeds BOOLEAN;
UPDATE starboards SET extra_embeds=true;
ALTER TABLE starboards ALTER COLUMN extra_embeds SET NOT NULL;