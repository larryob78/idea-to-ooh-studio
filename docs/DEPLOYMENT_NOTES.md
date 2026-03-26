# Deployment Notes

## Env vars
See `.env.example`.

## Migration strategy
- Run startup migration loader (`init_db`) on boot.
- For production, execute migrations explicitly in deployment step.

## Backups
- Database snapshots daily.
- Storage bucket versioning enabled.

## Monitoring
- Use `/metrics` endpoint and structured request IDs in logs.
