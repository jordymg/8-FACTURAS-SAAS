# ADR-0002: User-owned storage (Google Sheets + Drive)

**Date:** 2026-07-03
**Status:** Accepted

## Context
Storing invoice data and images ourselves adds cost, liability, and would complicate the $1,999 flat price. The deliverable to the accountant is a spreadsheet anyway.

## Decision
Each user's Google Sheet is the invoice datastore; original photos go to a folder in the user's own Google Drive. App DB holds only account/subscription state.

## Alternatives considered
- Own Postgres + S3 — rejected: cost, backup burden, users don't own their data
- Sheets only, no image storage — rejected: accountants need the source document

## Consequences
Zero storage cost, image backup included in the $1,999 plan, user owns everything. Constraint: requires Google account + OAuth verification for Sheets/Drive scopes (start early).
