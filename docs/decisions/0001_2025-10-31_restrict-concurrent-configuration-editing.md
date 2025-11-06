# 1: Restrict Concurrent Configuration Editing

Date: 2025-10-31

Status: Proposed

## Context and Problem Statement

When editing a configuration, the Refiner application does not store whether a
user is actively editing a configuration. This can lead to race conditions
issues when editing configurations. To avoid this, we're proposing having a
configuration locking mechanism that prevents conflicting changes and help
communicate clearly to the users who is currently making edits to a specific
configuration.

## Decision Drivers

- ⚔️ Prevent data loss and conflicting edits
- 📈 Improve user experience and clarity
- 🔏 Meet security and audit requirements
- ♿ Accessibility for all users
- 🏗️ Scalability for future growth

## Considered Options

| Option                               | Pros                                                | Cons                                                                  |
| ------------------------------------ | --------------------------------------------------- | --------------------------------------------------------------------- |
| Optimistic Locking (last-write-wins) | Simple to implement, no user blocking               | High risk of overwriting changes, poor user experience                |
| Manual Merge/Conflict Resolution     | Allows multiple editors, explicit conflict handling | Complex UI, high cognitive load, not suitable for non-technical users |
| ✅ Single-Editor Lock                | Clear ownership, prevents conflicts, simple UX      | Potential for lock contention, requires robust session management     |

## Decision Outcome

We will implement a single-editor lock system for configuration editing:

1. When a user opens a configuration for editing, a lock is acquired in the
   backend (DB table `configurations_locks`).
1. Other users accessing the same configuration are placed in view-only mode,
   with a banner indicating who is editing.
1. The lock is released when the user navigates away, logs out, or after a
   session timeout (default: 30 minutes, configurable).
1. Lock status is released via API (`DELETE /lock`). Lock status is presented to
   the frontend whenever a configuration is requested. So there's no need for an
   API endpoint for (`GET /lock`).
1. Frontend disables edit controls and displays clear notifications.
   Accessibility is ensured via ARIA-live banners and keyboard navigation.
1. Edge cases (browser close, disconnect, multiple tabs, impersonation) are
   handled by auto-releasing locks after timeout and always displaying the
   correct username from the backend.
1. Audit logs are maintained for lock activity, and monitoring is in place for
   stuck locks or frequent conflicts.

## Implementation Details

### Backend

- Add `configurations_locks` table with migration
- FastAPI endpoints for lock status/release
- Lock tied to user session; auto-release after timeout
- Audit trail for troubleshooting
- Configurable timeout via environment variable
- Lock released backend when user navigates away (browser unload, route change, logout)
- Expiry time set when lock acquired. Starts at time user opens a configuration
  for edit.
- Expiry resets on each user action (save, field change, other edit). Timeout always relative to latest activity.
- Backend only allows configuration edit/update if `userId` matches
  `lock.userId`.

#### Table: `configurations_locks`

Required columns:

- configuration_id (UUID, FK) // configId
- user_id (UUID, FK) // userId
- expires_at (TIMESTAMP) // expiryTime

Example (PostgreSQL):

```sql
CREATE TABLE configurations_locks (
  configuration_id UUID NOT NULL,
  user_id UUID NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  PRIMARY KEY (configuration_id),
  FOREIGN KEY (configuration_id) REFERENCES configurations(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Frontend

- Lock state managed via React hooks and Tanstack Query polling
- Banner for view-only and editing states, ARIA-live for accessibility
- Edit controls disabled when locked
- Cleanup on navigation, session expiry, and crashes

### Edge Cases

- Browser close/disconnect: lock auto-released after timeout
- Multiple tabs: same user/session can edit in parallel
- Impersonation: backend always returns correct username
- User inactivity: lock auto-released after timeout

### Security & Accessibility

- All lock API calls require authentication
- Only safe user info (username) returned
- Banner is ARIA-live, visible, and keyboard accessible

### Migration & Rollout

- DB migration for new table
- Backend endpoints deployed
- Frontend changes deployed
- Monitor for issues and iterate

### Testing

- Unit tests for backend API and DB lock logic
- Integration tests for frontend lock UX and view-only restrictions
- Accessibility tests for banner and controls
- Playwright tests require multiple users in local app to test locking

## Consequences

**Positive:**

- Prevents conflicting edits and data loss
- Improves user clarity and experience
- Provides auditability and security
- Accessible for all users

**Negative:**

- Users may experience lock contention
- Requires robust session and error handling
- Slight increase in backend and frontend complexity

## Appendix

- Related tickets: #423 (implementation), #571 (spike)
