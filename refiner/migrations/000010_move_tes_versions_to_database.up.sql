CREATE TABLE tes_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    is_current_tes_version BOOLEAN DEFAULT FALSE,
    version TEXT UNIQUE NOT NULL
);

ALTER TABLE configurations 
    ADD COLUMN tes_version TEXT,

    ADD CONSTRAINT fk_tes_version FOREIGN KEY (tes_version)
        REFERENCES tes_versions (version);


ALTER TABLE conditions 
    ADD CONSTRAINT fk_tes_version FOREIGN KEY (version)
        REFERENCES tes_versions (version);
