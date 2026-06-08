-- migrate:up

ALTER TABLE conditions_context_groupers
    ADD COLUMN completeness TEXT NOT NULL DEFAULT 'partially complete';

-- migrate:down

ALTER TABLE conditions_context_groupers
DROP COLUMN completeness;