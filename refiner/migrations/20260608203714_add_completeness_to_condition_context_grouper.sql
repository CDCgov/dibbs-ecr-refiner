-- migrate:up

ALTER TABLE conditions_context_groupers
ADD COLUMN completeness TEXT;

-- migrate:down

ALTER TABLE conditions_context_groupers
DROP COLUMN completeness;