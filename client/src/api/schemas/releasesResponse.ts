import type { Release } from './release';

/**
 * Response for releases as returned through the GitHub API.
 */
export interface ReleasesResponse {
  releases: Release[];
}
