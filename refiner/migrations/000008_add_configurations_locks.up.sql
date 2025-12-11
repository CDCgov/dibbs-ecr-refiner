-- Migration: Add configurations_locks table for configuration editing locks
CREATE TABLE configurations_locks (
  configuration_id UUID NOT NULL,
  user_id UUID NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  PRIMARY KEY (configuration_id),
  FOREIGN KEY (configuration_id) REFERENCES configurations(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);
