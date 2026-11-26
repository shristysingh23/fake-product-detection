# Fake Product Detection
AI-powered Android app that checks product packaging photos for signs of counterfeiting. It reads packaging text (OCR), detects logos and barcodes (YOLO), and compares images with genuine references to flag suspicious products. Built with Android, Spring Boot and FastAPI.

## Backend setup

Create a PostgreSQL database named `fake_product_detection`, then copy `backend/.env.example` and set the database variables in your shell:

```text
DB_URL=jdbc:postgresql://localhost:5432/fake_product_detection
DB_USERNAME=postgres
DB_PASSWORD=your-local-password
```

PowerShell example:

```powershell
$env:DB_URL="jdbc:postgresql://localhost:5432/fake_product_detection"
$env:DB_USERNAME="postgres"
$env:DB_PASSWORD="your-local-password"
```

Never commit `.env` files or database passwords. Flyway runs migrations automatically at startup. Hibernate is configured with `validate`, so schema changes must be expressed in `backend/src/main/resources/db/migration/`.

The first migration is `V1__create_products_table.sql`. It creates the `products` table only when absent, allowing an existing database to be migrated without dropping data. Do not run destructive database commands.

Run the backend:

```powershell
cd backend
.\mvnw spring-boot:run
```

Swagger UI is available at `http://localhost:8080/swagger-ui/index.html`. OpenAPI JSON is available at `http://localhost:8080/v3/api-docs`.

## Backend Product Management API

The Spring Boot backend exposes product reference data under `/api/products`.

### Endpoints

| Method | Path | Description | Success |
| --- | --- | --- | --- |
| `POST` | `/api/products` | Create a product | `201 Created` |
| `GET` | `/api/products` | List products with pagination and sorting | `200 OK` |
| `GET` | `/api/products/{id}` | Get a product by ID | `200 OK` |
| `PUT` | `/api/products/{id}` | Replace all editable product fields | `200 OK` |
| `DELETE` | `/api/products/{id}` | Delete a product | `204 No Content` |

Product creation and full updates require non-blank `brand` (up to 120 characters), `productName` (up to 200), and `category` (up to 100). Optional `barcode` is limited to 64 characters and optional `expectedText` to 5,000 characters.

### Pagination and sorting

`GET /api/products` supports these query parameters:

| Parameter | Default | Rules |
| --- | --- | --- |
| `page` | `0` | Zero or greater |
| `size` | `10` | From 1 to 100 |
| `sortBy` | `id` | `id`, `brand`, `productName`, `category`, `barcode`, or `expectedText` |
| `direction` | `ASC` | `ASC` or `DESC` |

Examples:

```text
GET http://localhost:8080/api/products
GET http://localhost:8080/api/products?page=1&size=5
GET http://localhost:8080/api/products?page=0&size=10&sortBy=brand&direction=ASC
GET http://localhost:8080/api/products?page=0&size=10&sortBy=category&direction=DESC
```

The list response is a Spring Data page with a `content` array and pagination metadata such as `number`, `size`, `totalElements`, and `totalPages`.

### Example requests

Create a product:

```http
POST /api/products
Content-Type: application/json

{
  "brand": "Acme",
  "productName": "Cereal",
  "category": "Food",
  "barcode": "0012345678905",
  "expectedText": "Genuine package text"
}
```

Replace a product:

```http
PUT /api/products/42
Content-Type: application/json

{
  "brand": "Acme",
  "productName": "Cereal",
  "category": "Food",
  "barcode": "0012345678905",
  "expectedText": "Genuine package text"
}
```

Retrieve or delete a product with `GET /api/products/42` or `DELETE /api/products/42`.

### Error responses

Errors use the same JSON structure. Validation and invalid pagination/query parameters return `400 Bad Request`; a missing product returns `404 Not Found`.

```json
{
  "status": 400,
  "error": "Bad Request",
  "message": "brand must not be blank"
}
```

## Phase 2: Genuine Product Reference Database

The backend has reference records for brands, product packaging versions, and reference-image metadata. Product's existing `brand` string remains for API compatibility; `brandId` optionally links it to a `Brand`. The existing Adidas Ultraboost product will be associated during the manual SQL migration without changing its original fields or ID.

```text
Brand 1 ───── * Product 1 ───── * ProductVersion 1 ───── * ProductReferenceImage
                   │                                       (metadata + local storage key)
                   └── existing product CRUD API
```

### Apply the manual PostgreSQL schema

Flyway is intentionally not used. Back up the database, then execute this one-time, idempotent script against the existing `fake_product_detection` database as a user with schema DDL privileges:

```powershell
psql -h localhost -U postgres -d fake_product_detection `
  -f backend/database/migrations/phase-2-reference-database.sql
```

The script creates `brands`, `product_versions`, and `product_reference_images`; adds a nullable `products.brand_id`; and links existing products to matching brand names. It does not drop tables or delete product rows. Inspect the script before applying it. Hibernate remains `ddl-auto=validate`; start the backend after migration and resolve any schema validation mismatch manually.

### Reference APIs

- Brands: `POST/GET /api/brands`, `GET/PUT/DELETE /api/brands/{id}`
- Product brand filtering: `GET /api/products?brandId={id}` (existing CRUD remains)
- Versions: `POST/GET /api/products/{productId}/versions`, `GET/PUT/DELETE /api/versions/{versionId}`
- Images: multipart `POST /api/versions/{versionId}/images` with `image` and `imageType`; `GET /api/versions/{versionId}/images`; `GET/DELETE /api/images/{imageId}`

Brand/version codes are unique (case-insensitive at the API/service level). Deletion is restricted when dependent products, versions or images exist. Errors use the existing `{status,error,message}` response shape.

### Local reference-image storage

Images are stored on local disk, not in PostgreSQL. Only image metadata and a generated `storageKey` are stored in the database. JPEG, PNG and WebP are accepted after content validation. The maximum size and local directory are configured with:

```text
REFERENCE_STORAGE_LOCAL_DIRECTORY=storage/reference-images
REFERENCE_STORAGE_MAX_FILE_SIZE=10485760
```

The directory is git-ignored. Image bytes are not served through a public URL by this phase; metadata provides the storage key for backend workflows.
