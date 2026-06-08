# PennyServ API and SaveBasket Data Platform Boundary

## Upstream Source of Truth

PennyServ API consumes normalized grocery intelligence from the upstream `savebasket-data-platform`.

The upstream platform remains source-of-truth for:

- normalized product catalog records
- normalized offer and promotion records
- price snapshots and aggregate pricing signals
- aggregate search features built from normalized data

## API Responsibilities

PennyServ API is responsible for customer-facing workflows only:

- search and ranking experiences
- receipt matching and post-purchase experiences
- basket optimization workflows
- watchlist and alerting workflows
- authentication and user-level personalization
- caching, readiness, and operational observability

## Explicit Non-Goals in This Repository

This API project does not implement:

- web scraping
- raw product ingestion
- raw offer parsing
- crawler normalization pipelines

## Integration Contract

All upstream reads must go through adapters in `src/integrations/data_platform`.

Adapter rules:

- use read-oriented APIs against normalized datasets
- keep transport concerns in client classes
- keep adapter contracts explicit and testable
- do not mutate upstream normalization state from this service
