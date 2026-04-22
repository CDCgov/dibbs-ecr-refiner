-- migrate:up
ALTER TABLE configurations_locks
  DROP CONSTRAINT configurations_locks_configuration_id_fkey,
  ADD CONSTRAINT configurations_locks_configuration_id_fkey
    FOREIGN KEY (configuration_id)
    REFERENCES configurations(id)
    ON DELETE CASCADE;

ALTER TABLE events
  DROP CONSTRAINT fk_configuration,
  ADD CONSTRAINT fk_events_configurations
    FOREIGN KEY (configuration_id)
    REFERENCES configurations(id)
    ON DELETE CASCADE;


-- migrate:down
ALTER TABLE configurations_locks
  DROP CONSTRAINT configurations_locks_configuration_id_fkey,
  ADD CONSTRAINT configurations_locks_configuration_id_fkey
    FOREIGN KEY (configuration_id)
    REFERENCES configurations(id);

ALTER TABLE events
  DROP CONSTRAINT fk_events_configurations,
  ADD CONSTRAINT fk_events_configurations
    FOREIGN KEY (configuration_id)
    REFERENCES configurations(id);
