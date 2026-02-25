# Billing and Limits

## Plans
- Pro
- Studio

Limits enforced:
- max projects
- max collaborators
- max storage GB
- max jobs/day
- max exports/day

## Stripe
- Endpoint: `POST /api/billing/stripe/webhook`
- Handles test-mode subscription create/update/delete events.
- Stores status in `subscriptions` table.

## Entitlement enforcement
- Project creation and job creation check plan limits.
- Returns `402` on limit breaches.
