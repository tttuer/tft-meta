# Backend Agent Memory

## Project Structure
- `backend/`: FastAPI application
- `backend/pipeline/`: Airflow DAGs and data processing scripts
- `contracts/api-spec.yaml`: API contract (MUST update after every backend change)

## Database Schema
- Primary key: UUID for most entities, `match_id` (String) for MatchRaw
- All tables have `created_at` and `updated_at` timestamps
- Migrations managed by Alembic

### Current Models
- **MatchRaw**: `match_id` (PK), `region`, `participants` (JSONB), `patch_version`, `collected_at`
- **Comp**: `id` (UUID PK), `name`, `tier`, stats fields, JSONB fields for units/positions
- **Champion**: TBD
- **Augment**: TBD
- **Item**: TBD

## API Integration
- Riot API rate limits: 20 req/1s, 100 req/2min
- Retry logic with exponential backoff in `app/services/riot_api.py`
- Redis caching: static data 1hr TTL, match data 24hr TTL

## Pipeline Architecture
- **fetch_matches.py**: Collects match data from Riot API
  - CLI options: `--region`, `--max-summoners`, `--dry-run`
  - Stores in `match_raw` table
- **analyze_comps.py**: Clustering and comp analysis
  - CLI options: `--date` (today/yesterday/YYYY-MM-DD), `--min-samples`
  - Default MIN_SAMPLE_COUNT=50, lower for testing

## Testing Configurations
- Use `--max-summoners 5` for ~50 matches (rate limit friendly)
- Use `--min-samples 20` for testing with small datasets
- Always use `--date today` when analyzing freshly collected data

## Environment Variables
- DATABASE_URL: PostgreSQL async connection
- RIOT_API_KEY: Riot Games API key
- REDIS_URL: Redis connection
- OPENROUTER_API_KEY: AI summary generation
- SLACK_WEBHOOK_URL: Pipeline notifications
