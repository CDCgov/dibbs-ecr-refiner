-- migrate:up

-- coverage level columns on the conditions table (from crmi-curationCoverageLevel extension)
ALTER TABLE conditions
    ADD COLUMN coverage_level text,
    ADD COLUMN coverage_level_reason text,
    ADD COLUMN coverage_level_date text;

ALTER TABLE conditions
    ADD CONSTRAINT coverage_level_check CHECK (
        -- all null: extension not present (older versions, conditions without the extension)
        (coverage_level IS NULL AND coverage_level_reason IS NULL AND coverage_level_date IS NULL)
        -- complete: no reason allowed, date is optional
        OR (coverage_level = 'complete' AND coverage_level_reason IS NULL)
        -- partial: reason required, no date
        OR (coverage_level = 'partial' AND coverage_level_reason IS NOT NULL AND coverage_level_date IS NULL)
    );

-- per-category additional context grouper detail
-- each row represents a single ACG ValueSet referenced by a condition grouper
CREATE TABLE conditions_context_groupers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    condition_id uuid NOT NULL REFERENCES conditions(id) ON DELETE CASCADE,

    name text NOT NULL,
    category text NOT NULL,
    canonical_url text NOT NULL,
    code_count integer NOT NULL DEFAULT 0,

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    UNIQUE (condition_id, canonical_url)
);

CREATE TRIGGER update_conditions_context_groupers_updated_at
BEFORE UPDATE ON conditions_context_groupers
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE INDEX conditions_context_groupers_condition_id_idx
    ON conditions_context_groupers(condition_id);

CREATE INDEX conditions_context_groupers_category_idx
    ON conditions_context_groupers(category);


-- migrate:down

DROP INDEX IF EXISTS conditions_context_groupers_category_idx;
DROP INDEX IF EXISTS conditions_context_groupers_condition_id_idx;

DROP TRIGGER IF EXISTS update_conditions_context_groupers_updated_at ON conditions_context_groupers;

DROP TABLE IF EXISTS conditions_context_groupers;

ALTER TABLE conditions
    DROP CONSTRAINT IF EXISTS coverage_level_check;

ALTER TABLE conditions
    DROP COLUMN IF EXISTS coverage_level_date,
    DROP COLUMN IF EXISTS coverage_level_reason,
    DROP COLUMN IF EXISTS coverage_level;
