-- migrate:up
CREATE TABLE active_payload_schema_reactivations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_schema_version INTEGER NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT active_payload_schema_reactivations_status_check
     CHECK (status IN ('IN_PROGRESS', 'COMPLETE', 'PARTIAL_FAILURE', 'FAILED')),

    CONSTRAINT active_payload_schema_reactivations_counts_check
     CHECK (success_count >= 0 AND failure_count >= 0)
);

CREATE INDEX active_payload_schema_reactivations_target_schema_version_idx
    ON active_payload_schema_reactivations (target_schema_version);

CREATE INDEX active_payload_schema_reactivations_status_idx
    ON active_payload_schema_reactivations (status);

CREATE UNIQUE INDEX active_payload_schema_reactivations_one_complete_per_version_idx
    ON active_payload_schema_reactivations (target_schema_version)
    WHERE status = 'COMPLETE';

-- migrate:down
DROP TABLE active_payload_schema_reactivations;

