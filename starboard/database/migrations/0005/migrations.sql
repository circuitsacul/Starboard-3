ALTER TABLE starboards ADD COLUMN xp_multiplier REAL;
ALTER TABLE starboards DROP COLUMN disable_xp;
ALTER TABLE starboards ALTER COLUMN xp_multiplier SET NOT NULL;
ALTER TABLE members ALTER COLUMN xp TYPE REAL USING xp::real;