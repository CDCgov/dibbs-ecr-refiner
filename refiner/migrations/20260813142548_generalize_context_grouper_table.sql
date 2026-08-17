-- migrate:up

ALTER TABLE conditions_context_groupers RENAME COLUMN name TO display_name;
ALTER TABLE conditions_context_groupers ADD COLUMN parent_url TEXT;
ALTER TABLE conditions_context_groupers RENAME TO valuesets;

ALTER TABLE conditions_codes
    DROP CONSTRAINT IF EXISTS conditions_codes_pkey;

-- create a new temp table to allow for unique primary key
CREATE TABLE conditions_codes_temp (
    condition_id UUID NOT NULL,
    code_id UUID NOT NULL,
    valueset_id UUID NOT NULL,
    is_child_rsg boolean DEFAULT false,

    PRIMARY KEY (condition_id, code_id, valueset_id),

    CONSTRAINT fk_condition_id_fkey
        FOREIGN KEY(condition_id)
        REFERENCES conditions(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_valueset_id_fkey
        FOREIGN KEY(valueset_id)
        REFERENCES valuesets(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_code_id_fkey
        FOREIGN KEY(code_id)
        REFERENCES codes(id)
        ON DELETE CASCADE
);


-- migrate:down
DROP TABLE conditions_codes_temp;

ALTER TABLE valuesets RENAME COLUMN display_name TO name;
ALTER TABLE valuesets DROP COLUMN parent_url;
ALTER TABLE valuesets RENAME TO conditions_context_groupers;
