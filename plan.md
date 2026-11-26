# Implementation Plan: AI-Based Product Authenticity and Verification System

**Date**: 2026-11-25 | **Spec**: AI-BASED FAKE PRODUCT DETECTION SYSTEM - Google Docs.pdf

## Summary

Build an MVP for initial verification of packaged food and beverage products. The system will let a consumer capture or upload an image, process it through the FastAPI AI service, compare it with verified Spring/PostgreSQL product references, and return an explainable status instead of a definitive authenticity claim. The Android/React Native client is the final user-facing increment; the first delivery is a working end-to-end backend and ML flow.

## Technical Context

- **Language/Version**: Java 25 with Spring Boot 4.1.2; Python with FastAPI/Pydantic
- **Primary Dependencies**: Spring Data JPA, Jakarta Validation, Spring WebMVC, PostgreSQL, Pillow/OpenCV, PaddleOCR/YOLO and visual embeddings as they are introduced
- **Storage**: PostgreSQL for structured records and verification history; local/object storage abstraction with AWS S3 as the production target
- **Testing**: JUnit and Spring tests; Pytest/TestClient; Maven and `pytest`
- **Target Platform**: Android MVP through React Native/TypeScript, with Spring Boot and FastAPI services
- **Performance Goals**: File uploads up to 10 MB; target ML response under 30 seconds; avoid false certainty
- **Constraints**: Initial scope is food and beverages; medicine verification is deferred; a photograph cannot establish product authenticity

## Constitution Check

- Safety over certainty: pass - every result must use an uncertainty-aware status and limitation text.
- Evidence separation: pass - submitted scans remain separate from verified reference records.
- No silent failures: pass - upstream ML, storage and database failures must map to explicit errors.
- Security: pass - authentication is required before verification history and user-owned records.
- Privacy: pass - image retention requires an explicit storage lifecycle and no unnecessary metadata collection.
- Reproducibility: pass - model versions and comparison inputs must be retained with verification evidence.

## Applied Guidelines

- Preserve the existing REST and DTO boundaries between `MlController`, `MlServiceClient` and FastAPI.
- Keep image validation at the API boundary and validate both declared MIME type and readable image bytes.
- Use transactional service methods and repository-backed entities for product records.
- Preserve JSON field names agreed in `ml-service/API_CONTRACT.md` unless the contract is explicitly versioned.
- Prefer small data/evidence models over a single monolithic verification payload.
- Keep medicine-specific rules, regulatory APIs and recall data out of the MVP; expose interfaces only where needed.

## Implementation Steps

### Step 1: [G2] Harden backend and data foundation
- **Group**: G2 - Spring backend
- **Requirements**: REQ-009, REQ-014
- **Design inputs**: Existing product entity, service, repository and API contract
- **Description**: Complete validated product/reference persistence, pagination, error handling and verification history entities. Add environment-based database configuration and remove credentials from source configuration.

### Step 2: [G4] Create reference and evidence data model
- **Group**: G4 - PostgreSQL storage
- **Requirements**: REQ-005, REQ-006, REQ-008, REQ-009
- **Design inputs**: Report database entity list
- **Description**: Model brands, manufacturers, products, reference images/metadata, identifiers, verification requests, evidence and reports while separating trusted references from user submissions.

### Step 3: [G3] Replace dummy ML response with preprocessing and OCR
- **Group**: G3 - FastAPI/ML
- **Requirements**: REQ-002, REQ-003, REQ-004
- **Design inputs**: `ml-service/app/main.py`, `ml-service/app/schemas.py`, API contract
- **Description**: Add image orientation/lighting preprocessing, region detection, PaddleOCR text extraction and category/brand/product identification with confidence scores.

### Step 4: [G3] Implement visual and identifier comparison
- **Group**: G3 - FastAPI/ML
- **Requirements**: REQ-005, REQ-006, REQ-007, REQ-008
- **Design inputs**: Research decisions and verified reference records
- **Description**: Compare logo and packaging embeddings against multiple genuine versions, detect barcode/QR text and evaluate batch/expiry consistency as evidence signals.

### Step 5: [G3] Implement anomaly scoring and evidence fusion
- **Group**: G3 - FastAPI/ML
- **Requirements**: REQ-010, REQ-011
- **Description**: Combine visual, OCR, identifier and reference evidence into an uncertainty-aware status: likely consistent, suspicious, verification required or insufficient evidence.

### Step 6: [G2] Implement verification workflow API
- **Group**: G2 - Spring backend
- **Requirements**: REQ-001, REQ-007, REQ-011, REQ-014
- **Design inputs**: Existing `MlController`, `MlServiceClient` and response DTOs
- **Description**: Accept image uploads, persist scan metadata, call FastAPI, store evidence/report data and enforce consistent error and timeout behavior.

### Step 7: [G1] Build React Native MVP
- **Group**: G1 - React Native mobile app
- **Requirements**: REQ-001, REQ-011, REQ-012, REQ-014
- **Design inputs**: Report scope and verification status taxonomy
- **Description**: Scaffold React Native/TypeScript, add camera/gallery upload, barcode scanning UI, verification status/report screens and history.

### Step 8: [G5] Validate MVP end to end
- **Group**: G5 - Cross-cutting
- **Requirements**: REQ-012
- **Description**: Run normal, low-light, blur, rotation, redesign and counterfeit-like test images; verify clear limitations and measure accuracy, false positives, recall and processing time.

### Step 9: [G5] Deploy and document MVP
- **Group**: G5 - Cross-cutting
- **Requirements**: REQ-011, REQ-012
- **Description**: Containerize backend and ML services, add CI checks, deployment configuration and user/developer documentation.

## Project Structure

```text
android-app/
  src/                    # React Native screens, components and API clients
backend/
  src/main/java/com/fpd/backend/
    entity/               # trusted and submitted data entities
    repository/
    service/
    controller/
    client/
    dto/
ml-service/
  app/
    preprocessing/
    detection/
    ocr/
    similarity/
    schemas.py
  tests/
docs/
plan.md
research.md
checkpoints/
```

## Testing Strategy

- **appType**: Mixed mobile + APIs
- **Critical user journeys**: upload/scan; OCR and evidence generation; suspicious/insufficient report; verification history; backend/ML failure handling
- **primaryValidationStack**: JUnit/Spring, Pytest/TestClient, React Native tests and Docker Compose
- **fallbackMatrix**:
  - `infra-tier`: PostgreSQL in Docker → local PostgreSQL or an isolated test instance
  - `browser-tier`: Expo/React Native emulator → API-level smoke tests with the existing backend
- **Environment requirements**: JDK 25, Maven, Python/venv, PostgreSQL, Node/npm, Android emulator or device
- **knownGaps**: Local emulation cannot prove camera quality or real manufacturer API availability
- **Test data strategy**: Synthetic genuine/reference sets plus independently obtained or clearly licensed samples; separate train/test/holdout data
- **Acceptance criteria**: All image upload and report flows return explicit statuses; invalid and unavailable evidence are not converted into “genuine”; critical backend/ML tests pass

## Tasks

### Phase 1: Setup

- [ ] T001 [G2] [Plan:1.1] Replace PostgreSQL credentials in `backend/src/main/resources/application.properties` with environment variables and add safe `.env.example` documentation.
- [ ] T002 [G3] [Plan:3.1] Add ML dependencies for image preprocessing and OCR to `ml-service/requirements.txt` with pinned versions.
- [ ] T003 [G1] [Plan:7.1] Scaffold the React Native TypeScript application under `android-app/`.
- [ ] T004 [G5] [P] [Plan:9.1] Add Docker Compose configuration for PostgreSQL, the Spring backend and the FastAPI ML service.

### Phase 2: Foundational data and contracts

- [ ] T005 [G4] [Plan:2.1] Create Brand, Manufacturer, ProductReference, ProductIdentifier, VerificationRecord, VerificationEvidence and VerificationReport entities in `backend/src/main/java/com/fpd/backend/entity/`.
- [ ] T006 [G4] [P] [Plan:2.1] Create repositories for the verification entities in `backend/src/main/java/com/fpd/backend/repository/`.
- [ ] T007 [G2] [Plan:1.1] Add verification DTO request/response contracts under `backend/src/main/java/com/fpd/backend/dto/`.
- [ ] T008 [G3] [Plan:5.1] Extend `ml-service/app/schemas.py` with category, OCR, similarity, anomaly, evidence, status and limitation fields while retaining backward-compatible client parsing.
- [ ] T009 [G2] [Plan:6.1] Add upload size/type validation and configurable limits to `backend/src/main/java/com/fpd/backend/controller/MlController.java`.
- [ ] T010 [G2] [Plan:1.1] Add explicit storage configuration and a retention policy abstraction in `backend/src/main/java/com/fpd/backend/config/`.

### Phase 3: User Story 1 - Upload and scan a product (P1)

- [ ] T011 [P] [G1] [US1] [Plan:7.1] Add camera and image-picker support in `android-app/src/screens/ScanScreen.tsx`.
- [ ] T012 [P] [G1] [US1] [Plan:7.1] Add multipart upload and API client code in `android-app/src/services/verificationApi.ts`.
- [ ] T013 [G3] [US1] [Plan:3.1] Implement image preprocessing and orientation correction in `ml-service/app/preprocessing/`.
- [ ] T014 [G3] [US1] [Plan:3.1] Implement region detection and OCR in `ml-service/app/detection/` and `ml-service/app/ocr/`.
- [ ] T015 [G2] [US1] [Plan:6.1] Add the verification upload workflow to `backend/src/main/java/com/fpd/backend/service/VerificationService.java`.
- [ ] T016 [G2] [US1] [Plan:6.1] Expose `/api/verifications` upload and retrieval endpoints in `backend/src/main/java/com/fpd/backend/controller/VerificationController.java`.

### Phase 4: User Story 2 - Compare visual evidence (P1)

- [ ] T017 [G4] [US2] [Plan:2.1] Seed a version-aware reference schema and representative genuine records in `backend/src/main/resources/`.
- [ ] T018 [G3] [US2] [Plan:4.1] Implement logo and packaging embedding extraction in `ml-service/app/similarity/`.
- [ ] T019 [G3] [US2] [Plan:3.1] Detect and extract barcode/QR values and package text regions in `ml-service/app/detection/`.
- [ ] T020 [G3] [US2] [Plan:4.1] Compare the submitted image against multiple genuine reference versions and return per-evidence scores.
- [ ] T021 [G3] [US2] [Plan:4.1] Add OCR batch/expiry/date consistency checks in `ml-service/app/ocr/`.

### Phase 5: User Story 3 - Produce explainable report (P1)

- [ ] T022 [G3] [US3] [Plan:5.1] Implement anomaly and evidence-fusion scoring in `ml-service/app/`.
- [ ] T023 [G3] [US3] [Plan:5.1] Replace `ANALYSIS_PENDING` with the four-status taxonomy and limitation text in `ml-service/app/main.py`.
- [ ] T024 [G2] [US3] [Plan:6.1] Persist verification evidence and reports in `backend/src/main/java/com/fpd/backend/service/VerificationService.java`.
- [ ] T025 [G1] [US3] [Plan:7.1] Implement verification status, evidence and limitation screens in `android-app/src/screens/ReportScreen.tsx`.
- [ ] T026 [G1] [US3] [Plan:7.1] Implement verification history in `android-app/src/screens/HistoryScreen.tsx`.

### Phase 6: Authentication and verification history (P2)

- [ ] T027 [G2] [Plan:1.1] Implement JWT authentication and protected verification endpoints in `backend/src/main/java/com/fpd/backend/config/` and `backend/src/main/java/com/fpd/backend/controller/`.
- [ ] T028 [G1] [Plan:7.1] Add login/session handling and API authorization in `android-app/src/`.
- [ ] T029 [G4] [Plan:2.1] Link verification records and reports to authenticated users in `backend/src/main/java/com/fpd/backend/entity/`.

### Phase 7: Validation and deployment

- [ ] T030 [G3] [P] [Plan:8.1] Add holdout image tests covering low light, blur, rotation, reflections and packaging redesigns in `ml-service/tests/`.
- [ ] T031 [G2] [P] [Plan:8.1] Add integration tests for upload, timeout, upstream error and verification persistence in `backend/src/test/java/com/fpd/backend/`.
- [ ] T032 [G1] [P] [Plan:8.1] Add mobile camera/upload/report smoke tests under `android-app/src/tests/`.
- [ ] T033 [G5] [Plan:9.1] Add CI jobs for Maven, Pytest and React Native validation in `.github/workflows/`.
- [ ] T034 [G5] [Plan:9.1] Add backend and ML Dockerfiles plus deployment environment documentation in `docs/`.
- [ ] T035 [G5] [Plan:9.1] Document accuracy metrics, false-positive rate, rejection rate, inference time and product verification limitations in `docs/`.

## Requirement Mapping

| REQ ID | Description | Plan Items | Implementation Evidence |
|--------|-------------|------------|-------------------------|
| REQ-001 | Capture or upload product photographs | P6.1, P7.1 | VerificationController.java, MlController.java, ScanScreen.tsx |
| REQ-002 | Identify product category and brand | P3.1 | detection/ modules, OCR response schema |
| REQ-003 | Extract packaging text with OCR | P3.1 | ml-service/app/ocr/, schemas.py |
| REQ-004 | Detect product, logo, package, barcode and identifier regions | P3.1 | ml-service/app/detection/ |
| REQ-005 | Compare uploaded logo with genuine references | P4.1 | ml-service/app/similarity/ |
| REQ-006 | Compare packaging layout, colours, fonts and graphics | P2.1, P4.1 | reference entities, similarity modules |
| REQ-007 | Detect and check barcode/QR identifiers | P4.1, P6.1 | ML detection, verification workflow |
| REQ-008 | Analyse batch, manufacturing and expiry information | P2.1, P4.1 | OCR checks, verification evidence entities |
| REQ-009 | Maintain verified genuine product references | P1.1, P2.1 | ProductReference entities/repositories and seed data |
| REQ-010 | Detect previously unseen anomalies | P5.1 | anomaly fusion module and evidence scores |
| REQ-011 | Generate explainable verification reports | P5.1, P6.1, P7.1 | VerificationReport, ReportScreen.tsx |
| REQ-012 | Deliver a packaged food and beverage MVP | P8.1, P9.1 | end-to-end tests and deployment docs |
| REQ-013 | Defer the medicine module until the core workflow is reliable | P5.1, P9.1 | medicine interfaces excluded and roadmap documented |
| REQ-014 | Maintain authenticated verification history | P1.1, P6.1, P7.1 | auth configuration, user-linked records, HistoryScreen.tsx |
