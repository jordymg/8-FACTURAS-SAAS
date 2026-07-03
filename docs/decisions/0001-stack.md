# ADR-0001: Stack — PWA + Flask + Gemini + Render

**Date:** 2026-07-03
**Status:** Accepted

## Context
Prototype already exists in Flask/Python with Gemini extraction (~90% accuracy). Founder needs lowest-friction path to production and a single service that also hosts a landing page.

## Decision
PWA frontend + Flask backend + Gemini for extraction, deployed as a single Render web service.

## Alternatives considered
- Next.js/Node rewrite — rejected: throws away a working prototype
- VPS — rejected: more ops work, no benefit at this scale
- Traditional web hosting (cPanel) — rejected: can't run Python backend

## Consequences
One deployable, auto-deploy from GitHub. Render free tier sleeps (~30s cold start); acceptable for validation, upgrade (~USD 7/mo) at launch.
