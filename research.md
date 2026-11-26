# Research Decisions

## Decision: React Native with TypeScript for the mobile MVP

**Rationale**: It matches the project report and supports a shared Android/iOS codebase. Android will be the initial validation target.

**Alternatives considered**: Native Android/Kotlin and separate iOS apps were deferred due to longer duplication; Android-only Kotlin could be added later.

## Decision: An evidence-fusion workflow instead of a definitive classifier

**Rationale**: Copied barcodes and legitimate packaging revisions make a photo-only authentic/fake label unsafe. The MVP will return one of four statuses and explain limitations.

**Alternatives considered**: A binary fake/genuine model was rejected because it would hide uncertainty and increase false-positive risk.

## Decision: PostgreSQL first, AWS S3 behind a storage interface

**Rationale**: PostgreSQL is already configured and sufficient for MVP records. Object storage can be introduced without coupling the verification workflow to AWS.

**Alternatives considered**: Directly storing images in PostgreSQL was rejected for scale and lifecycle reasons.

## Decision: Multiple genuine reference versions are mandatory

**Rationale**: Redesigns across markets, years and batch packaging must not be treated as suspicious. Reference records need market/version metadata.

**Alternatives considered**: One reference image per product was rejected as too brittle.

## Decision: The pharmaceutical module remains deferred

**Rationale**: Medicine verification requires reliable regulatory/manufacturer mechanisms and has higher safety consequences. The implementation will not imply medical verification in the MVP.

**Alternatives considered**: Packaging-only medicine checks were rejected because they can appear genuine while the contents or supply chain are not.
