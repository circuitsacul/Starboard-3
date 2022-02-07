ALTER TABLE starboards RENAME allow_explore TO private;
UPDATE starboards SET private = NOT (private);