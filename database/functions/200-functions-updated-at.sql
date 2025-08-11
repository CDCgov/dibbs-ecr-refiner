-- Simple function to automatically update the updated_at timestamp
-- This function is intentionally kept very simple for easy understanding and maintenance
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
