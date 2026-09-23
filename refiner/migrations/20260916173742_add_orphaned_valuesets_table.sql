-- migrate:up

-- quarantine for valueset rows the processed TES tables no longer declare
--
-- the seeder upserts conditions and valuesets but rebuilds the membership
-- junction wholesale, so a leaf grouper that disappears upstream used to stay
-- in `valuesets` forever: unreferenced by any membership, invisible to the
-- membership checks, and still served by the condition detail endpoint. the
-- seeder now moves those rows here instead of leaving or dropping them
--
-- deliberately free of foreign keys. The condition a row pointed at may itself
-- be gone, and a quarantine that can be broken by a later delete is not a
-- quarantine, so every identifying value is denormalized as text
CREATE TABLE orphaned_valuesets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- identity the row had in `valuesets`, for matching against an old dump
    valueset_id UUID NOT NULL,
    canonical_url TEXT NOT NULL,
    condition_canonical_url TEXT NOT NULL,
    condition_version TEXT NOT NULL,

    display_name TEXT,
    category TEXT,
    code_count INTEGER,
    completeness TEXT,
    parent_url TEXT,

    -- 0 means the row was already stranded before this run; anything higher
    -- means this seed is what retired it, which is the distinction that says
    -- whether a removal is routine or a surprise
    memberships_at_removal INTEGER NOT NULL,

    valueset_created_at TIMESTAMPTZ NOT NULL,
    valueset_updated_at TIMESTAMPTZ NOT NULL,
    removed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- migrate:down

DROP TABLE orphaned_valuesets;
