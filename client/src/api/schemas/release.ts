import type { ReleaseNotes } from './releaseNotes';

/**
 * Type for release information sent to the frontend.
 */
export interface Release {
  id: string;
  created_at: string;
  name: string;
  release_notes: ReleaseNotes[];
  prerelease: boolean;
  url: string;
}
