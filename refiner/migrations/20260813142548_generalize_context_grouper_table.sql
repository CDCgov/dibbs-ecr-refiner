-- migrate:up

ALTER TABLE conditions_context_groupers RENAME COLUMN name TO display_name;
ALTER TABLE conditions_context_groupers ADD COLUMN parent_url TEXT;
ALTER TABLE conditions_context_groupers RENAME TO valuesets;

ALTER TABLE conditions_codes
    DROP CONSTRAINT IF EXISTS conditions_codes_pkey;

CREATE TABLE conditions_codes_temp (
    condition_id UUID CONSTRAINT ,
    code_id uuid CONSTRAINT conditions_rsg_codes_code_id_not_null NOT NULL,
    valueset_id uuid
    is_child_rsg boolean DEFAULT false,
    
    UNIQUE (condition_id, canonical_url, valueset_id)

    CONSTRAINT fk_condition_id_fkey
        FOREIGN KEY(condition_id) 
        REFERENCES conditions(id)
        ON DELETE CASCADE

    CONSTRAINT fk_valueset_id_fkey
        FOREIGN KEY(valueset_id) 
        REFERENCES valuesets(id)
        ON DELETE CASCADE

    CONSTRAINT fk_code_id_fkey
        FOREIGN KEY(code_id) 
        REFERENCES codes(id)
        ON DELETE CASCADE
);


-- migrate:down
ALTER TABLE conditions_codes
    DROP CONSTRAINT IF EXISTS fk_conditions_valuesets_fkey;

DROP TABLE conditions_codes_temp;

ALTER TABLE conditions_codes DROP COLUMN valueset_id;

ALTER TABLE conditions_valuesets RENAME COLUMN display_name TO name;
ALTER TABLE conditions_valuesets DROP COLUMN parent_url;
ALTER TABLE conditions_valuesets RENAME TO conditions_context_groupers;
